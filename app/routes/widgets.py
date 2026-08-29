from fastapi import APIRouter, Depends
from app.db import get_db
from app.auth import get_current_tenant_id
from app.schemas.widget_schemas import WidgetCreate, WidgetUpdate, WidgetOut
from app.services import widget_service, submission_service

router = APIRouter(prefix="/widgets", tags=["widgets"])

@router.post("", response_model=WidgetOut, status_code=201)
def create_widget(data: WidgetCreate, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return widget_service.create_widget(conn, tenant_id, data)

@router.get("", response_model=list[WidgetOut])
def list_widgets(conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return widget_service.list_widgets(conn, tenant_id)

@router.get("/{widget_id}", response_model=WidgetOut)
def get_widget(widget_id: str, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return widget_service.get_widget(conn, widget_id, tenant_id)

@router.patch("/{widget_id}", response_model=WidgetOut)
def update_widget(widget_id: str, data: WidgetUpdate, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return widget_service.update_widget(conn, widget_id, tenant_id, data)

@router.delete("/{widget_id}", status_code=204)
def delete_widget(widget_id: str, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    widget_service.delete_widget(conn, widget_id, tenant_id)

@router.get("/{widget_id}/submissions")
def list_submissions(widget_id: str, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return submission_service.list_submissions_for_widget(conn, widget_id, tenant_id)

@router.get("/{widget_id}/stats")
def get_stats(widget_id: str, conn=Depends(get_db), tenant_id: str = Depends(get_current_tenant_id)):
    return submission_service.get_stats_for_widget(conn, widget_id, tenant_id)