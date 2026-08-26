from fastapi import APIRouter, Depends, Request
from app.db import get_db
from app.schemas.submission_schemas import SubmissionCreate, SubmissionOut
from app.services import submission_service
from app.services.rate_limit import limiter

router = APIRouter(tags=["submissions"])

@router.post("/submissions", response_model=SubmissionOut, status_code=201)
@limiter.limit("10/minute")
def submit(data: SubmissionCreate, request: Request, conn=Depends(get_db)):
    ip_address = request.client.host
    return submission_service.create_submission(conn, data, ip_address)