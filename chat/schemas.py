from datetime import timedelta
from typing import Annotated

from django.db.models import Q
from django.utils import timezone
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema

from .models import Message, Room


class RoomIn(ModelSchema):
    class Meta:
        model = Room
        fields = ["name", "topic"]


class RoomOut(ModelSchema):
    class Meta:
        model = Room
        fields = ["id", "name", "topic", "created_at"]


class Conflict(Schema):
    message: str
    existing_id: int


class RoomFilter(FilterSchema):
    search: Annotated[str | None, FilterLookup("name__icontains")] = None
    topic: Annotated[str | None, FilterLookup("topic__icontains")] = None
    recent: bool | None = None

    def filter_recent(self, value: bool) -> Q:
        week_ago = timezone.now() - timedelta(days=7)
        return Q(created_at__gte=week_ago) if value else Q(created_at__lt=week_ago)

class MessageIn(ModelSchema):
    class Meta:
        model = Message
        fields = ["content"]


class MessageOut(ModelSchema):
    room: RoomOut

    class Meta:
        model = Message
        fields = ["id", "author", "content", "created_at"]
