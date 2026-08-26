from fastapi import APIRouter, Depends, Request
from app.db import get_db
from app.schemas.submission_schemas import SubmissionCreate, SubmissionOut
from app.services import submission_service
from app.services.rate_limit import limiter
from app.services.submission_service import safe_ip

router = APIRouter(tags=["submissions"])

@router.post("/submissions", response_model=SubmissionOut, status_code=201)
@limiter.limit("10/minute")
def submit(request: Request, data: SubmissionCreate, conn=Depends(get_db)):
    raw_ip = request.client.host if request.client else None
    ip_address = safe_ip(raw_ip)
    return submission_service.create_submission(conn, data, ip_address)