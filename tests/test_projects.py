# tests/test_projects.py
from projects.models import Role


def test_create_project(alice, client_for):
    response = client_for(alice).post(
        "/projects/", json={"name": "Launch", "description": "Product launch"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Launch"
    assert data["task_count"] == 0
    assert alice.memberships.get(project_id=data["id"]).role == Role.OWNER


def test_list_only_my_projects(alice, carol, project, client_for):
    client_for(carol).post(
        "/projects/", json={"name": "Carol's garden", "description": "Vegetables"}
    )

    response = client_for(alice).get("/projects/")
    assert [p["name"] for p in response.json()] == ["Website redesign"]


def test_non_member_gets_404(carol, project, client_for):
    response = client_for(carol).get(f"/projects/{project.id}")
    assert response.status_code == 404


def test_member_cannot_delete(bob, project, client_for):
    response = client_for(bob).delete(f"/projects/{project.id}")
    assert response.status_code == 403
    assert response.json() == {"detail": "This needs the owner role"}


def test_owner_can_update(alice, project, client_for):
    response = client_for(alice).put(
        f"/projects/{project.id}", json={"name": "Website v2", "description": "Round two"}
    )
    assert response.status_code == 200
    project.refresh_from_db()
    assert project.name == "Website v2"


def test_add_member_twice(alice, bob, project, client_for):
    response = client_for(alice).post(f"/projects/{project.id}/members", json={"username": "bob"})
    assert response.status_code == 409
    assert response.json() == {"detail": "bob is already a member"}
