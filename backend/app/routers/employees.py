"""Employees: add / edit / delete, and upload their photos (a folder, or one zip for everyone)."""
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Employee, User, get_db
from ..face.dataset import count_faces, make_label, read_zip, save_faces, save_profile_photo
from ..schemas import EmployeeIn, EmployeeOut, EmployeeUpdate
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/api", tags=["employees"])


def to_out(emp: Employee) -> EmployeeOut:
    out = EmployeeOut.model_validate(emp)
    out.has_photo = bool(emp.photo_path)
    out.face_images = count_faces(emp.label)
    return out


def new_code(db: Session) -> str:
    n = db.query(Employee).count() + 1
    while db.query(Employee).filter(Employee.employee_code == f"ONX{n:04d}").first():
        n += 1
    return f"ONX{n:04d}"


def get_or_404(db: Session, emp_id: int) -> Employee:
    emp = db.get(Employee, emp_id)
    if emp is None:
        raise HTTPException(404, "Employee not found.")
    return emp


def add_photos(db: Session, emp: Employee, files) -> dict:
    report = save_faces(emp.label, files)
    first = report.pop("first_good_image")
    if first and not emp.photo_path:
        emp.photo_path = save_profile_photo(emp.label, first)
        db.commit()
    return report


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [to_out(e) for e in db.query(Employee).order_by(Employee.name)]


@router.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(body: EmployeeIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    label = make_label(body.label or body.name)
    if db.query(Employee).filter(Employee.label == label).first():
        raise HTTPException(409, f"An employee with label '{label}' already exists.")
    emp = Employee(**body.model_dump(exclude={"label"}), label=label, employee_code=new_code(db))
    db.add(emp)
    db.commit()
    return to_out(emp)


@router.patch("/employees/{emp_id}", response_model=EmployeeOut)
def update_employee(emp_id: int, body: EmployeeUpdate, _: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    emp = get_or_404(db, emp_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)
    db.commit()
    return to_out(emp)


@router.delete("/employees/{emp_id}", status_code=204)
def delete_employee(emp_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Deletes the employee AND their face photos (privacy). Retrain afterwards."""
    emp = get_or_404(db, emp_id)
    shutil.rmtree(settings.FACES_DIR / emp.label, ignore_errors=True)
    (settings.PHOTOS_DIR / f"{emp.label}.jpg").unlink(missing_ok=True)
    db.delete(emp)
    db.commit()


@router.get("/employees/{emp_id}/photo")
def employee_photo(emp_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emp = get_or_404(db, emp_id)
    if not emp.photo_path:
        raise HTTPException(404, "No photo.")
    return FileResponse(emp.photo_path, media_type="image/jpeg")


@router.post("/employees/{emp_id}/images")
async def upload_photos(emp_id: int, files: list[UploadFile] = File(...),
                        _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """A folder (or several photos) of ONE person."""
    emp = get_or_404(db, emp_id)
    photos = [((f.filename or "photo").split("/")[-1], await f.read()) for f in files]
    return add_photos(db, emp, photos)


@router.post("/enroll/zip")
async def upload_zip(file: UploadFile = File(...), _: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    """ONE zip with a folder per person, e.g. 'project 1/udit/*.jpg'. New folders = new employees."""
    try:
        people = read_zip(await file.read())
    except Exception as exc:
        raise HTTPException(400, f"Could not read the zip: {exc}")
    report = []
    for label, photos in sorted(people.items()):
        emp = db.query(Employee).filter(Employee.label == label).first()
        created = emp is None
        if created:
            emp = Employee(label=label, name=label.replace("_", " ").title(), employee_code=new_code(db))
            db.add(emp)
            db.commit()
        r = add_photos(db, emp, photos)
        report.append({"label": label, "name": emp.name, "created": created, "saved": r["saved"],
                       "skipped": len(r["skipped"]), "total_faces": r["total_faces"]})
    return {"people": report, "total_saved": sum(p["saved"] for p in report),
            "total_skipped": sum(p["skipped"] for p in report)}
