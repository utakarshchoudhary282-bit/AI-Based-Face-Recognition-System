"""Verification logs and the numbers on the Verify page."""
from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import Employee, User, VerificationLog, get_db
from ..face.service import face_service
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/logs")
def logs(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(VerificationLog).order_by(VerificationLog.id.desc()).limit(300)
    return [{"id": r.id, "checked_by": r.checked_by, "result": r.result, "similarity": r.similarity,
             "predicted_label": r.predicted_label, "employee_name": r.employee.name if r.employee else None,
             "created_at": r.created_at} for r in rows]


@router.get("/stats")
def stats(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    total = db.query(VerificationLog).count()
    matches = db.query(VerificationLog).filter(VerificationLog.result == "MATCH").count()
    return {"employees": db.query(Employee).count(),
            "model_ready": face_service.ready,
            "people_in_model": len(face_service.model.people) if face_service.ready else 0,
            "checks_today": db.query(VerificationLog).filter(VerificationLog.created_at >= today).count(),
            "match_rate": round(matches / total, 3) if total else None}
