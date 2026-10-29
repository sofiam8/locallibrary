
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from ninja import FilterLookup, FilterSchema, ModelSchema, Schema, UploadedFile
from pydantic import AfterValidator, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from accounts.schemas import UserOut
from projects.schemas import LabelOut
from .models import Attachment, Comment, Priority, Task, TaskStatus


class TaskUpdate(ModelSchema):
    priority: Priority = Priority.MEDIUM

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "due_date"]

    @field_validator("title", "description", "priority", check_fields=False)
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise PydanticCustomError(
                "not_null",
                "This field can't be null",
            )
        return value

    @field_validator("title", check_fields=False)
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise PydanticCustomError(
                "blank",
                "Title can't be blank",
            )
        return value


class TaskIn(TaskUpdate):
    assignee_id: int | None = Field(
        None,
        description="A member of the project",
        examples=[2],
    )
    label_ids: list[int] = Field(
        default_factory=list,
        description="Labels of the same project",
        examples=[[1]],
    )

    @model_validator(mode="after")
    def urgent_needs_due_date(self):
        if self.priority == Priority.URGENT and self.due_date is None:
            raise ValueError("Urgent tasks need a due date")
        return self


class StatusIn(Schema):
    status: TaskStatus


class TaskOut(ModelSchema):
    assignee: UserOut | None
    labels: list[LabelOut]
    status: TaskStatus
    priority: Priority

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "due_date",
            "created_at",
        ]


class CommentIn(ModelSchema):
    class Meta:
        model = Comment
        fields = ["body"]


class CommentOut(ModelSchema):
    author: UserOut

    class Meta:
        model = Comment
        fields = ["id", "body", "created_at"]


class TaskFilter(FilterSchema):
    status: Annotated[
        list[TaskStatus] | None,
        FilterLookup("status__in"),
    ] = None

    assignee: Annotated[
        str | None,
        FilterLookup("assignee__username"),
    ] = None

    label: Annotated[
        str | None,
        FilterLookup("labels__name"),
    ] = None

    due_before: Annotated[
        date | None,
        FilterLookup("due_date__lt"),
    ] = None

    search: Annotated[
        str | None,
        FilterLookup(["title__icontains", "description__icontains"]),
    ] = Field(
        None,
        description="Text to find in the title or the description",
    )


TaskOrdering = Literal[
    "created_at",
    "-created_at",
    "due_date",
    "-due_date",
    "priority",
    "-priority",
]


MAX_UPLOAD_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".md",
}


def check_upload(file: UploadedFile) -> UploadedFile:
    if file.size > MAX_UPLOAD_SIZE:
        raise PydanticCustomError(
            "file_too_large",
            "Files can be at most 5 MB",
        )

    if Path(file.name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise PydanticCustomError(
            "file_type",
            "Only PDF, PNG, JPEG and text files are allowed",
        )

    return file


AttachmentFile = Annotated[
    UploadedFile,
    AfterValidator(check_upload),
]


class AttachmentIn(Schema):
    name: str = Field("", max_length=200)


class AttachmentOut(ModelSchema):
    uploaded_by: UserOut
    url: str

    class Meta:
        model = Attachment
        fields = ["id", "name", "uploaded_at"]

    @staticmethod
    def resolve_url(obj, context):
        return context["request"].build_absolute_uri(obj.file.url)
