"""The RAG assistant and the policy documents it reads."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import Employee, User, get_db
from ..rag.assistant import answer
from ..rag.documents import list_policies
from ..rag.llm import get_llm
from ..schemas import AskIn
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/assistant/ask")
def ask(body: AskIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    employee = None
    if body.employee_id is not None:
        employee = db.get(Employee, body.employee_id)
        if employee is None:
            raise HTTPException(404, "Employee not found.")
    return answer(body.question.strip(), employee)


@router.get("/assistant/status")
def status(_: User = Depends(get_current_user)):
    return {"llm": "Groq (Llama 3.1)" if get_llm() else "none (no API key)",
            "policies": len(list_policies())}


@router.get("/policies")
def policies(_: User = Depends(get_current_user)):
    return list_policies()
