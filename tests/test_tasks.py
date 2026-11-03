# tests/test_tasks.py
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from tasks.models import Priority, Task, TaskStatus


@pytest.fixture
def task(project, alice):
    return project.tasks.create(title="Draft the sitemap", assignee=alice)


def test_create_task(alice, bob, project, client_for):
    label = project.labels.create(name="design")
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/",
        json={"title": "  Pick fonts ", "assignee_id": bob.id, "label_ids": [label.id]},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Pick fonts"
    assert data["assignee"]["username"] == "bob"
    assert data["labels"] == [{"id": label.id, "name": "design", "color": "#808080"}]
    assert data["status"] == "todo"


def test_blank_title(alice, project, client_for):
    response = client_for(alice).post(f"/projects/{project.id}/tasks/", json={"title": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {"type": "blank", "loc": ["body", "payload", "title"], "msg": "Title can't be blank"}
    ]


def test_urgent_task_needs_due_date(alice, project, client_for):
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/", json={"title": "Fix login", "priority": Priority.URGENT}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, Urgent tasks need a due date"


def test_assignee_must_be_member(alice, carol, project, client_for):
    response = client_for(alice).post(
        f"/projects/{project.id}/tasks/", json={"title": "Pick fonts", "assignee_id": carol.id}
    )
    assert response.status_code == 400


def test_non_member_cannot_see_tasks(carol, task, client_for):
    response = client_for(carol).get(f"/projects/{task.project_id}/tasks/{task.id}")
    assert response.status_code == 404


def test_patch_changes_only_sent_fields(alice, task, client_for):
    response = client_for(alice).patch(
        f"/projects/{task.project_id}/tasks/{task.id}", json={"due_date": "2026-10-15"}
    )
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.due_date == date(2026, 10, 15)
    assert task.title == "Draft the sitemap"

# tests/test_tasks.py
@pytest.mark.parametrize(
    "old, new, status_code",
    [
        (TaskStatus.TODO, TaskStatus.IN_PROGRESS, 200),
        (TaskStatus.IN_PROGRESS, TaskStatus.DONE, 200),
        (TaskStatus.TODO, TaskStatus.DONE, 409),
        (TaskStatus.DONE, TaskStatus.TODO, 409),
    ],
)
def test_status_transitions(alice, task, client_for, old, new, status_code):
    Task.objects.filter(id=task.id).update(status=old)
    response = client_for(alice).post(
        f"/projects/{task.project_id}/tasks/{task.id}/status", json={"status": new}
    )
    assert response.status_code == status_code

# tests/test_tasks.py
@pytest.fixture
def sample_tasks(project, bob):
    bug = project.labels.create(name="bug")
    project.tasks.create(
        title="Fix mobile menu", assignee=bob, priority=Priority.URGENT, due_date=date(2026, 10, 1)
    ).labels.add(bug)
    project.tasks.create(
        title="Set up analytics",
        description="Page views",
        status=TaskStatus.IN_PROGRESS,
        due_date=date(2026, 10, 20),
    )
    project.tasks.create(
        title="Compress images",
        assignee=bob,
        priority=Priority.HIGH,
        due_date=date(2026, 10, 3),
        status=TaskStatus.DONE,
    )


@pytest.mark.parametrize(
    "query, titles",
    [
        ("", ["Fix mobile menu", "Set up analytics", "Compress images"]),
        ("status=todo&status=in_progress", ["Fix mobile menu", "Set up analytics"]),
        ("assignee=bob&label=bug", ["Fix mobile menu"]),
        ("due_before=2026-10-05", ["Fix mobile menu", "Compress images"]),
        ("search=VIEWS", ["Set up analytics"]),
        ("ordering=-priority", ["Fix mobile menu", "Compress images", "Set up analytics"]),
    ],
)
def test_filter_tasks(alice, project, sample_tasks, client_for, query, titles):
    response = client_for(alice).get(f"/projects/{project.id}/tasks/?{query}")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()["items"]] == titles
    assert response.json()["count"] == len(titles)

# tests/test_tasks.py
def test_only_author_can_edit_comment(alice, bob, task, client_for):
    comment = task.comments.create(author=bob, body="Looks good")
    url = f"/projects/{task.project_id}/tasks/{task.id}/comments/{comment.id}"

    response = client_for(alice).put(url, json={"body": "Changed"})
    assert response.status_code == 403

    response = client_for(alice).delete(url)  # the owner may delete it
    assert response.status_code == 204


def test_upload_attachment(alice, task, client_for, settings):
    file = SimpleUploadedFile("notes.txt", b"Remember the footer")
    response = client_for(alice).post(
        f"/projects/{task.project_id}/tasks/{task.id}/attachments",
        data={"name": "Meeting notes"},
        FILES={"file": file},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Meeting notes"
    assert data["url"].startswith("http://testlocation/media/attachments/")

    attachment = task.attachments.get()
    assert (settings.MEDIA_ROOT / attachment.file.name).read_bytes() == b"Remember the footer"


def test_upload_rejects_file_type(alice, task, client_for):
    file = SimpleUploadedFile("setup.exe", b"MZ")
    response = client_for(alice).post(
        f"/projects/{task.project_id}/tasks/{task.id}/attachments", FILES={"file": file}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "file_type"
    assert not task.attachments.exists()


def test_delete_attachment(alice, bob, task, client_for, settings):
    file = SimpleUploadedFile("plan.pdf", b"%PDF-1.4")
    attachment = task.attachments.create(file=file, name="plan.pdf", uploaded_by=alice)
    url = f"/projects/{task.project_id}/tasks/{task.id}/attachments/{attachment.id}"

    response = client_for(bob).delete(url)
    assert response.status_code == 403

    response = client_for(alice).delete(url)
    assert response.status_code == 204
    assert not (settings.MEDIA_ROOT / attachment.file.name).exists()
