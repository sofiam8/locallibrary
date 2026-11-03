# tests/conftest.py
import pytest
from django.contrib.auth.models import User
from ninja.testing import TestClient

from accounts.tokens import create_token_pair
from projects.models import Project, Role
from taskflow.api import api


@pytest.fixture(autouse=True)
def test_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path  # uploads go to a temporary folder
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def alice(db):
    return User.objects.create_user("alice", password="wonderland-42")


@pytest.fixture
def bob(db):
    return User.objects.create_user("bob", password="builder-42")


@pytest.fixture
def carol(db):
    return User.objects.create_user("carol", password="sunflower-77")


@pytest.fixture
def project(alice, bob):
    """Alice owns the project, bob is a member."""
    project = Project.objects.create(name="Website redesign", description="New marketing site")
    project.memberships.create(user=alice, role=Role.OWNER)
    project.memberships.create(user=bob, role=Role.MEMBER)
    return project


@pytest.fixture
def client_for():
    """Return a TestClient that is logged in as the given user."""

    def make_client(user):
        token = create_token_pair(user.id)["access"]
        return TestClient(api, headers={"Authorization": f"Bearer {token}"})

    return make_client
