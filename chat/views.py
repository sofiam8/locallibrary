
from django.shortcuts import render

from .models import Room


def index(request):
    return render(request, "chat/index.html")


def room(request, room_name):
    room = Room.objects.filter(name=room_name).first()
    chat_messages = room.messages.all() if room else []

    return render(
        request,
        "chat/room.html",
        {
            "room_name": room_name,
            "chat_messages": chat_messages,
        },
    )
