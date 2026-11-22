"""Train the model, and verify a photo."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Employee, User, VerificationLog, get_db
from ..face import sface_model
from ..face.detector import extract_face
from ..face.service import face_service
from ..security import get_current_user, require_admin
from .employees import to_out

router = APIRouter(prefix="/api", tags=["recognition"])

# Which zones each access level opens (same table as the Access Control Policy, section 3)
ZONES = {
    "L1": ["Lobby", "Cafeteria", "Ground-floor meeting rooms"],
    "L2": ["Office work floors", "Library", "Training rooms"],
    "L3": ["R&D lab", "Network operations room", "Records room"],
    "L4": ["Server room (data centre)", "Finance vault"],
}
WARNINGS = {
    "On Leave": "Employee is ON LEAVE: entry only with HR/manager approval; no L3/L4 zones.",
    "Suspended": "Employee is SUSPENDED: deny entry and inform HR.",
    "Exited": "Employee has LEFT the company: treat as a visitor.",
}


def allowed_zones(level: str, status: str) -> list[str]:
    if status in ("Suspended", "Exited"):
        return []
    top = int(level[1])
    if status == "On Leave":
        top = min(top, 2)
    return [zone for n in range(1, top + 1) for zone in ZONES[f"L{n}"]]


@router.post("/train", status_code=202)
def train(_: User = Depends(require_admin)):
    try:
        face_service.start_training()
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    return face_service.status


@router.get("/train/status")
def training_status(_: User = Depends(require_admin)):
    return {**face_service.status, "model_ready": face_service.ready}


@router.get("/train/metrics")
def training_metrics(_: User = Depends(require_admin)):
    return sface_model.load_metrics()          # null until the first training


@router.post("/verify")
async def verify(file: UploadFile = File(...), user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if not face_service.ready:
        raise HTTPException(409, "No trained model yet. An admin must upload photos and train.")
    try:
        face, box = extract_face(await file.read())
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    log = VerificationLog(checked_by=user.user_id)
    if face is None:
        log.result = "NO_FACE"
        db.add(log)
        db.commit()
        return {"result": "NO_FACE", "employee": None, "top": [],
                "message": "No face found. Retake the photo facing the camera, in good light."}

    top = face_service.predict(face)                    # top 3 guesses
    result = face_service.decide(top)                   # MATCH or UNKNOWN
    names = {e.label: e for e in db.query(Employee).filter(Employee.label.in_([t["label"] for t in top]))}
    for t in top:
        t["name"] = names[t["label"]].name if t["label"] in names else t["label"]
    emp = names.get(top[0]["label"]) if result == "MATCH" else None

    log.predicted_label, log.similarity, log.result = top[0]["label"], top[0]["similarity"], result
    log.employee_id = emp.id if emp else None
    db.add(log)
    db.commit()

    response = {"result": result, "similarity": top[0]["similarity"], "threshold": settings.SIMILARITY_THRESHOLD,
                "top": top, "face_box": box, "employee": None, "warning": None, "allowed_zones": []}
    if emp:
        response.update(employee=to_out(emp).model_dump(), warning=WARNINGS.get(emp.status),
                        allowed_zones=allowed_zones(emp.access_level, emp.status),
                        message=f"Verified as {emp.name}.")
    else:
        response["message"] = (f"Similarity {top[0]['similarity']:.2f} is below {settings.SIMILARITY_THRESHOLD}: "
                                "UNKNOWN person. Check their ID card and call their manager.")
    return response
