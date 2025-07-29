from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from .core import get_memory_payload


def register_ping(app, route="/__ping__"):
    router = APIRouter()

    @router.get(route)
    async def ping():
        return JSONResponse(content=get_memory_payload(), headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

    app.include_router(router)
