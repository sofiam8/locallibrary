
from ninja import ModelSchema, Schema

from accounts.schemas import UserOut
from .models import Label, Project, Role


class LabelIn(ModelSchema):
    class Meta:
        model = Label
        fields = ["name", "color"]


class LabelOut(ModelSchema):
    class Meta:
        model = Label
        fields = ["id", "name", "color"]


class ProjectIn(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectOut(ModelSchema):
    labels: list[LabelOut]
    task_count: int
    unassigned_task_count: int

    class Meta:
        model = Project
        fields = ["id", "name", "description", "created_at"]


class MemberIn(Schema):
    username: str
    role: Role = Role.MEMBER


class MemberOut(Schema):
    user: UserOut
    role: Role
