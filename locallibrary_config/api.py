from ninja import NinjaAPI
from ninja.security import django_auth

from chat.api import router as rooms_router

api = NinjaAPI(auth=django_auth)

api.add_router("/rooms", rooms_router)
