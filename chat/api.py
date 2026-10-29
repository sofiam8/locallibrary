from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from .models import Message, Room
from .schemas import Conflict, MessageIn, MessageOut, RoomFilter, RoomIn, RoomOut

router = Router(tags=["rooms"])


@router.get("/", response=list[RoomOut], auth=None)
@paginate
def list_rooms(request, filters: Query[RoomFilter]):
    return filters.filter(Room.objects.order_by("name"))


@router.get("/mine", response=list[MessageOut])
def my_messages(request):
    return Message.objects.filter(author=request.auth).select_related("room")


@router.get("/{room_id}", response=RoomOut, auth=None)
def get_room(request, room_id: int):
    return get_object_or_404(Room, id=room_id)


@router.post("/", response={201: RoomOut, 409: Conflict})
def create_room(request, payload: RoomIn):
    existing = Room.objects.filter(name=payload.name).first()
    if existing:
        return Status(
            409,
            {
                "message": "A room with that name already exists",
                "existing_id": existing.id,
            },
        )
    return Status(201, Room.objects.create(**payload.dict()))


@router.put("/{room_id}", response=RoomOut)
def update_room(request, room_id: int, payload: RoomIn):
    room = get_object_or_404(Room, id=room_id)
    for attr, value in payload.dict().items():
        setattr(room, attr, value)
    room.save()
    return room


@router.delete("/{room_id}", response={204: None})
def delete_room(request, room_id: int):
    get_object_or_404(Room, id=room_id).delete()


@router.get("/{room_id}/messages", response=list[MessageOut], auth=None)
@paginate
def list_messages(request, room_id: int):
    room = get_object_or_404(Room, id=room_id)
    return room.messages.select_related("room")


@router.post("/{room_id}/messages", response={201: MessageOut})
def post_message(request, room_id: int, payload: MessageIn):
    room = get_object_or_404(Room, id=room_id)

    if not payload.content.strip():
        raise HttpError(400, "Messages can't be blank")

    message = Message.objects.create(
        room=room,
        author=request.auth,
        content=payload.content,
    )

    async_to_sync(get_channel_layer().group_send)(
        f"chat_{room.name}",
        {"type": "chat.message", "message": message.content},
    )

    return message
