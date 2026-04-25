from fastapi import FastAPI

from app.api.routes.activity import router as activity_router
from app.api.routes.comments import router as comments_router
from app.api.routes.issues import router as issues_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.projects import router as projects_router
from app.api.routes.sprints import router as sprints_router
from app.api.routes.watchers import router as watchers_router
from app.api.routes.workflow import router as workflow_router
from app.api.routes.ws import router as ws_router
from app.api.routes.search import router as search_router


def create_app() -> FastAPI:
    app = FastAPI(title="Project Management Platform API", version="0.1.0")
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(issues_router, prefix="/api", tags=["issues"])
    app.include_router(sprints_router, prefix="/api", tags=["sprints"])
    app.include_router(workflow_router, prefix="/api", tags=["workflow"])
    app.include_router(activity_router, prefix="/api", tags=["activity"])
    app.include_router(comments_router, prefix="/api", tags=["comments"])
    app.include_router(watchers_router, prefix="/api", tags=["watchers"])
    app.include_router(notifications_router, prefix="/api", tags=["notifications"])
    app.include_router(ws_router)
    app.include_router(search_router, prefix="/api", tags=["search"])

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
