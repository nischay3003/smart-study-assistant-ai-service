from fastapi import APIRouter, WebSocket

from app.streaming.manager import manager

router = APIRouter()


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str
):

    await manager.connect(chat_id, websocket)

    try:

        while True:
            await websocket.receive_text()

    except Exception:

        manager.disconnect(chat_id)