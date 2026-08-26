from fastapi import HTTPException
from app.repositories import widget_repo, submission_repo
import ipaddress

def safe_ip(ip: str) -> str | None:
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        return None


def create_submission(conn, data, ip_address: str):
    widget = widget_repo.get_by_id(conn, str(data.widget_id))
    if not widget or not widget["is_active"]:
        raise HTTPException(status_code=404, detail="Widget not found")

    return submission_repo.insert(
        conn,
        widget_id=str(data.widget_id),
        tenant_id=widget["tenant_id"],
        name=data.name,
        email=data.email,
        age=data.age,
        gender=data.gender,
        message=data.message,
        ip_address= safe_ip(ip_address),
        country=None,
        city=None,
        honeypot_triggered=False,
        status="stored",
    )