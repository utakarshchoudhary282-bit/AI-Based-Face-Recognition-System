"""Command-line helpers (run from the backend folder):

  python -m scripts.manage import-folder "D:\\project 1"          # one sub-folder of photos per person
  python -m scripts.manage import-zip "project 1.zip"              # the same, from a zip
  python -m scripts.manage details scripts/employees.sample.json   # fill in employee details
  python -m scripts.manage train                                   # train and print the scores
  python -m scripts.manage add-user guard1 "Gate Security" Guard@123 --role security
"""
import argparse
import json
from pathlib import Path

from app.db import Employee, SessionLocal, User, init_db
from app.face import sface_model
from app.face.dataset import IMAGE_EXTS, load_training_set, make_label, read_zip, save_faces, save_profile_photo
from app.security import ensure_default_admin, hash_password


def enrol(people: dict):
    db = SessionLocal()
    for label, photos in sorted(people.items()):
        emp = db.query(Employee).filter(Employee.label == label).first()
        if emp is None:
            emp = Employee(label=label, name=label.title(), employee_code=f"ONX{db.query(Employee).count() + 1:04d}")
            db.add(emp)
            db.commit()
        report = save_faces(label, photos)
        if report["first_good_image"] and not emp.photo_path:
            emp.photo_path = save_profile_photo(label, report["first_good_image"])
            db.commit()
        print(f"{label:12s} saved {report['saved']:3d}   skipped {len(report['skipped'])}")
    db.close()


def read_folder(root: Path) -> dict:
    people = {}
    for person in sorted(p for p in root.iterdir() if p.is_dir()):
        photos = [(f.name, f.read_bytes()) for f in sorted(person.iterdir()) if f.suffix.lower() in IMAGE_EXTS]
        if photos:
            people[make_label(person.name)] = photos
    return people


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import-folder").add_argument("path")
    sub.add_parser("import-zip").add_argument("path")
    sub.add_parser("details").add_argument("path")
    sub.add_parser("train")
    u = sub.add_parser("add-user")
    u.add_argument("user_id")
    u.add_argument("full_name")
    u.add_argument("password")
    u.add_argument("--role", default="security", choices=["admin", "security"])
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        ensure_default_admin(db)

    if args.cmd == "import-folder":
        enrol(read_folder(Path(args.path)))
    elif args.cmd == "import-zip":
        enrol(read_zip(Path(args.path).read_bytes()))
    elif args.cmd == "details":
        with SessionLocal() as db:
            for row in json.loads(Path(args.path).read_text()):
                emp = db.query(Employee).filter(Employee.label == row["label"]).first()
                if emp:
                    for key, value in row.items():
                        if key != "label":
                            setattr(emp, key, value)
                    print("updated", row["label"])
            db.commit()
    elif args.cmd == "train":
        images, labels = load_training_set()
        print(f"Training on {len(labels)} photos of {len(set(labels))} people...")
        m = sface_model.train(images, labels)
        print(f"Accuracy {m['accuracy']:.1%} | precision {m['precision']:.2f} | recall {m['recall']:.2f} "
              f"| F1 {m['f1']:.2f} ({m['folds']}-fold cross-validation)")
    elif args.cmd == "add-user":
        with SessionLocal() as db:
            db.add(User(user_id=args.user_id, full_name=args.full_name,
                        password_hash=hash_password(args.password), role=args.role))
            db.commit()
        print("created", args.user_id)


if __name__ == "__main__":
    main()
