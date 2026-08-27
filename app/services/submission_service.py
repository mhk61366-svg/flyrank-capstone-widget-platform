from fastapi import HTTPException
from app.repositories import widget_repo, submission_repo
import ipaddress
from app.services import spam_check, geo_enrichment, notify

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

    if spam_check.is_spam(data.hp_field):
        return submission_repo.insert(
            conn, widget_id=str(data.widget_id), tenant_id=widget["tenant_id"],
            name=data.name, email=data.email, age=data.age, gender=data.gender,
            message=data.message, ip_address=ip_address, country=None, city=None,
            honeypot_triggered=True, status="rejected_spam",
        )
    geo = geo_enrichment.enrich(ip_address)
    submission = submission_repo.insert(
        conn, widget_id=str(data.widget_id), tenant_id=widget["tenant_id"], name=data.name, email=data.email,
        age=data.age, gender=data.gender, message=data.message, ip_address=ip_address, country=geo["country"],
        city=geo["city"], honeypot_triggered=False, status="stored",
        )
    
    try:
        notify.send_confirmation(data.email, str(widget_id))
    except Exception as e:
        print(f"[NOTIFY ERROR] failed to notify {data.email}: {e}")
    return submission