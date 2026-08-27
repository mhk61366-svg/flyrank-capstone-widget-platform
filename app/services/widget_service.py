from fastapi import HTTPException
from app.repositories import widget_repo
from app.config import API_BASE_URL, WIDGET_JS_VERSION


def with_snippet(widget: dict) -> dict:
    widget = dict(widget)
    widget["embed_snippet"] = (
        f'<script src="{API_BASE_URL}/widget.js?id={widget["id"]}&v={WIDGET_JS_VERSION}"></script>'
    )
    return widget

def create_widget(conn, tenant_id: str, data):
    return with_snippet(widget_repo.create(conn, tenant_id, data.title, data.description, data.button_text))

def list_widgets(conn, tenant_id: str):
    return [with_snippet(w) for w in widget_repo.list_for_tenant(conn, tenant_id)]

def get_widget(conn, widget_id: str, tenant_id: str):
    widget = widget_repo.get_owned(conn, widget_id, tenant_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return with_snippet(widget)

def update_widget(conn, widget_id: str, tenant_id: str, data):
    fields = data.model_dump(exclude_unset=True)
    widget = widget_repo.update_owned(conn, widget_id, tenant_id, fields)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return with_snippet(widget)

def delete_widget(conn, widget_id: str, tenant_id: str):
    if not widget_repo.delete_owned(conn, widget_id, tenant_id):
        raise HTTPException(status_code=404, detail="Widget not found")

