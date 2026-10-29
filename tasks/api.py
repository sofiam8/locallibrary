
from django.shortcuts import get_object_or_404

from ninja import File, Form, PatchDict, Path, Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import CursorPagination, PageNumberPagination, paginate

from projects.models import Role
from projects.permissions import get_project_or_404

from .models import ALLOWED_TRANSITIONS, Priority, Task
from .schemas import (
    AttachmentFile,
    AttachmentIn,
    AttachmentOut,
    CommentIn,
    CommentOut,
    StatusIn,
    TaskFilter,
    TaskIn,
    TaskOrdering,
    TaskOut,
    TaskUpdate,
)


router = Router(tags=["tasks"])


def get_task_or_404(user, project_id, task_id):
    project = get_project_or_404(user, project_id)
    return get_object_or_404(project.tasks, id=task_id)


def check_relations(project, payload):
    assignee_id = payload.assignee_id

    if (
        assignee_id is not None
        and not project.memberships.filter(user_id=assignee_id).exists()
    ):
        raise HttpError(
            400,
            f"User {assignee_id} is not a member of this project",
        )

    labels = list(project.labels.filter(id__in=payload.label_ids))

    if len(labels) != len(set(payload.label_ids)):
        raise HttpError(400, "Unknown label id for this project")

    return labels


@router.get("/", response=list[TaskOut])
@paginate(PageNumberPagination, page_size=20)
def list_tasks(
    request,
    project_id: Path[int],
    filters: Query[TaskFilter],
    ordering: TaskOrdering = "created_at",
):
    """List the tasks of a project, 20 per page. Filters combine with AND."""
    project = get_project_or_404(request.auth, project_id)

    tasks = filters.filter(
        project.tasks.select_related("assignee").prefetch_related("labels")
    )

    return tasks.order_by(ordering, "id")


@router.post("/", response={201: TaskOut})
def create_task(request, project_id: Path[int], payload: TaskIn):
    project = get_project_or_404(request.auth, project_id)
    labels = check_relations(project, payload)

    task = Task.objects.create(
        project=project,
        **payload.dict(exclude={"label_ids"}),
    )

    task.labels.set(labels)

    return Status(201, task)


@router.get("/{task_id}", response=TaskOut)
def get_task(request, project_id: Path[int], task_id: int):
    return get_task_or_404(request.auth, project_id, task_id)


@router.patch("/{task_id}", response=TaskOut)
def update_task(
    request,
    project_id: Path[int],
    task_id: int,
    payload: PatchDict[TaskUpdate],
):
    task = get_task_or_404(request.auth, project_id, task_id)

    for attr, value in payload.items():
        setattr(task, attr, value)

    if task.priority == Priority.URGENT and task.due_date is None:
        raise HttpError(400, "Urgent tasks need a due date")

    task.save()

    return task


@router.post(
    "/{task_id}/status",
    response=TaskOut,
    summary="Move a task to another status",
)
def change_status(
    request,
    project_id: Path[int],
    task_id: int,
    payload: StatusIn,
):
    """
    Allowed moves:

    - `todo` to `in_progress`
    - `in_progress` to `todo` or `done`
    - `done` to `in_progress`

    Any other move returns **409 Conflict**.
    """
    task = get_task_or_404(request.auth, project_id, task_id)

    if payload.status not in ALLOWED_TRANSITIONS[task.status]:
        raise HttpError(
            409,
            f"Can't move a task from {task.status} to {payload.status}",
        )

    task.status = payload.status
    task.save()

    return task


@router.get("/{task_id}/comments", response=list[CommentOut])
@paginate(CursorPagination, ordering=("id",), page_size=20)
def list_comments(request, project_id: Path[int], task_id: int):
    task = get_task_or_404(request.auth, project_id, task_id)
    return task.comments.select_related("author")


@router.post("/{task_id}/comments", response={201: CommentOut})
def add_comment(
    request,
    project_id: Path[int],
    task_id: int,
    payload: CommentIn,
):
    task = get_task_or_404(request.auth, project_id, task_id)

    return Status(
        201,
        task.comments.create(
            author=request.auth,
            body=payload.body,
        ),
    )


@router.put("/{task_id}/comments/{comment_id}", response=CommentOut)
def update_comment(
    request,
    project_id: Path[int],
    task_id: int,
    comment_id: int,
    payload: CommentIn,
):
    task = get_task_or_404(request.auth, project_id, task_id)
    comment = get_object_or_404(task.comments, id=comment_id)

    if comment.author != request.auth:
        raise HttpError(403, "Only the author can edit a comment")

    comment.body = payload.body
    comment.save()

    return comment


@router.delete(
    "/{task_id}/comments/{comment_id}",
    response={204: None},
)
def delete_comment(
    request,
    project_id: Path[int],
    task_id: int,
    comment_id: int,
):
    task = get_task_or_404(request.auth, project_id, task_id)
    comment = get_object_or_404(task.comments, id=comment_id)

    if comment.author != request.auth:
        get_project_or_404(
            request.auth,
            project_id,
            roles=[Role.OWNER],
        )

    comment.delete()

    return Status(204, None)


@router.get("/{task_id}/attachments", response=list[AttachmentOut])
def list_attachments(request, project_id: Path[int], task_id: int):
    task = get_task_or_404(request.auth, project_id, task_id)

    return task.attachments.select_related(
        "uploaded_by"
    ).order_by("id")


@router.post(
    "/{task_id}/attachments",
    response={201: AttachmentOut},
)
def upload_attachment(
    request,
    project_id: Path[int],
    task_id: int,
    details: Form[AttachmentIn],
    file: File[AttachmentFile],
):
    task = get_task_or_404(request.auth, project_id, task_id)

    attachment = task.attachments.create(
        file=file,
        name=details.name or file.name,
        uploaded_by=request.auth,
    )

    return Status(201, attachment)


@router.delete(
    "/{task_id}/attachments/{attachment_id}",
    response={204: None},
)
def delete_attachment(
    request,
    project_id: Path[int],
    task_id: int,
    attachment_id: int,
):
    task = get_task_or_404(request.auth, project_id, task_id)
    attachment = get_object_or_404(
        task.attachments,
        id=attachment_id,
    )

    if attachment.uploaded_by != request.auth:
        get_project_or_404(
            request.auth,
            project_id,
            roles=[Role.OWNER, Role.ADMIN],
        )

    attachment.file.delete(save=False)
    attachment.delete()

    return Status(204, None)
