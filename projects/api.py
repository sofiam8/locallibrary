
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from ninja import Router, Status
from ninja.errors import HttpError

from .models import Project, Role
from .permissions import get_project_or_404
from .schemas import (
    LabelIn,
    LabelOut,
    MemberIn,
    MemberOut,
    ProjectIn,
    ProjectOut,
)


router = Router(tags=["projects"])


def projects_with_counts(user):
    return (
        Project.objects.filter(memberships__user=user)
        .annotate(
            task_count=Count("tasks"),
            unassigned_task_count=Count(
                "tasks",
                filter=Q(tasks__assignee=None),
            ),
        )
        .prefetch_related("labels")
    )


@router.get("/", response=list[ProjectOut])
def list_projects(request):
    return projects_with_counts(request.auth).order_by("id")


@router.post("/", response={201: ProjectOut})
def create_project(request, payload: ProjectIn):
    project = Project.objects.create(**payload.dict())

    project.memberships.create(
        user=request.auth,
        role=Role.OWNER,
    )

    return Status(
        201,
        projects_with_counts(request.auth).get(id=project.id),
    )


@router.get("/{project_id}", response=ProjectOut)
def get_project(request, project_id: int):
    return get_object_or_404(
        projects_with_counts(request.auth),
        id=project_id,
    )


@router.put("/{project_id}", response=ProjectOut)
def update_project(request, project_id: int, payload: ProjectIn):
    project = get_project_or_404(
        request.auth,
        project_id,
        roles=[Role.OWNER, Role.ADMIN],
    )

    for attr, value in payload.dict().items():
        setattr(project, attr, value)

    project.save()

    return projects_with_counts(request.auth).get(id=project.id)


@router.delete("/{project_id}", response={204: None})
def delete_project(request, project_id: int):
    project = get_project_or_404(
        request.auth,
        project_id,
        roles=[Role.OWNER],
    )

    project.delete()

    return Status(204, None)


@router.post("/{project_id}/labels", response={201: LabelOut})
def create_label(request, project_id: int, payload: LabelIn):
    project = get_project_or_404(
        request.auth,
        project_id,
        roles=[Role.OWNER, Role.ADMIN],
    )

    label = project.labels.create(**payload.dict())

    return Status(201, label)


@router.get("/{project_id}/members", response=list[MemberOut])
def list_members(request, project_id: int):
    project = get_project_or_404(request.auth, project_id)

    return project.memberships.select_related("user").order_by("id")


@router.post("/{project_id}/members", response={201: MemberOut})
def add_member(request, project_id: int, payload: MemberIn):
    project = get_project_or_404(
        request.auth,
        project_id,
        roles=[Role.OWNER],
    )

    user = User.objects.filter(
        username=payload.username,
    ).first()

    if user is None:
        raise HttpError(
            400,
            f"User {payload.username} does not exist",
        )

    if project.memberships.filter(user=user).exists():
        raise HttpError(
            409,
            f"{user.username} is already a member",
        )

    membership = project.memberships.create(
        user=user,
        role=payload.role,
    )

    return Status(201, membership)
