from fastapi import HTTPException
from app.repositories import widget_repo

def create_widget(conn, tenant_id: str, data):
    return widget_repo.create(conn, tenant_id, data.title, data.description, data.button_text)

def list_widgets(conn, tenant_id: str):
    return widget_repo.list_for_tenant(conn, tenant_id)

def get_widget(conn, widget_id: str, tenant_id: str):
    widget = widget_repo.get_owned(conn, widget_id, tenant_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

def update_widget(conn, widget_id: str, tenant_id: str, data):
    fields = data.model_dump(exclude_unset=True)
    widget = widget_repo.update_owned(conn, widget_id, tenant_id, fields)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

def delete_widget(conn, widget_id: str, tenant_id: str):
    if not widget_repo.delete_owned(conn, widget_id, tenant_id):
        raise HTTPException(status_code=404, detail="Widget not found")