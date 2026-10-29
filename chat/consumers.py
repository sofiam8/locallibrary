
import json
from channels.db import aclose_old_connections
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, Room


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Find or create the room in the database
        await aclose_old_connections()
        self.room, _ = await Room.objects.aget_or_create(
            name=self.room_name
        )

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Save message to the database
        await aclose_old_connections()
        user = self.scope["user"]

        await Message.objects.acreate(
            room=self.room,
            author=user if user.is_authenticated else None,
            content=message,
        )

        # Broadcast message to everyone in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": message},
        )

    async def chat_message(self, event):
        message = event["message"]
        await self.send(
            text_data=json.dumps({"message": message})
        )
