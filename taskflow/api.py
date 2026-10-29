
from ninja import NinjaAPI
from accounts.auth import JWTAuth


DESCRIPTION = (
    "Track the tasks of your team's projects: members, labels, "
    "comments and attachments.\n\n"
    "Get a token from `POST /auth/token`, then click "
    "**Authorize** and paste it."
)


api = NinjaAPI(
    title="TaskFlow API",
    version="1.0",
    description=DESCRIPTION,
    urls_namespace="taskflow",
    auth=JWTAuth(),
)

api.add_router("/auth", "accounts.api.router")
api.add_router("/auth", "accounts.api.tokens")
api.add_router("/projects", "projects.api.router")
api.add_router(
    "/projects/{project_id}/tasks",
    "tasks.api.router",
)


@api.get("/health", auth=None, include_in_schema=False)
def health(request):
    return {"status": "ok"}


api_v2 = NinjaAPI(
    title="TaskFlow API",
    version="2.0",
    description=(
        DESCRIPTION
        + "\n\nNew in 2.0: token responses use OAuth2 field names."
    ),
    urls_namespace="taskflow-v2",
    auth=JWTAuth(),
)

api_v2.add_router("/auth", "accounts.api.router")
api_v2.add_router("/auth", "accounts.api_v2.tokens")
api_v2.add_router("/projects", "projects.api.router")
api_v2.add_router(
    "/projects/{project_id}/tasks",
    "tasks.api.router",
)
