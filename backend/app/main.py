from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import analytics_router, events_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Urban Fleet AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(events_router)
app.include_router(analytics_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
