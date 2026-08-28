import os
from fastapi import APIRouter, Depends, HTTPException, Response
from app.db import get_db
from app.repositories import widget_repo

router = APIRouter(tags=["widget-public"])

WIDGET_JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "widget.js")
with open(WIDGET_JS_PATH) as f:
    WIDGET_JS_CONTENT = f.read()

@router.get("/widgets/{widget_id}/config")
def get_widget_config(widget_id: str, response: Response, conn=Depends(get_db)):
    widget = widget_repo.get_by_id(conn, widget_id)
    if not widget or not widget["is_active"]:
        raise HTTPException(status_code=404, detail="Widget not found")
    response.headers["Cache-Control"] = "public, max-age=60"
    return {
        "id": str(widget["id"]),
        "title": widget["title"],
        "description": widget["description"],
        "button_text": widget["button_text"],
    }

@router.get("/widget.js")
def get_widget_js():
    return Response(
        content=WIDGET_JS_CONTENT,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )