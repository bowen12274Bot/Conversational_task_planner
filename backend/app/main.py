from fastapi import FastAPI

from app.api.routes import router as api_router


app = FastAPI(title="Conversational Task Planner API")
app.include_router(api_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
