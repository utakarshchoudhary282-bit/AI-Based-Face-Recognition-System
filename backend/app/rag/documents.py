"""The knowledge base: the 5 policy files, cut into small chunks for searching."""
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from ..config import settings


def load_policy_chunks() -> list[Document]:
    """Split each policy by its '## ' headings, then into ~700-character chunks.
    Every chunk starts with '[Policy > Section]' so it still makes sense on its own."""
    by_heading = MarkdownHeaderTextSplitter([("#", "title"), ("##", "section")], strip_headers=False)
    by_size = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    chunks = []
    for path in sorted(settings.POLICY_DIR.glob("*.md")):
        for part in by_heading.split_text(path.read_text(encoding="utf-8")):
            title = part.metadata.get("title", path.stem)
            section = part.metadata.get("section", "")
            for piece in by_size.split_text(part.page_content):
                chunks.append(Document(page_content=f"[{title} > {section}] {piece}",
                                       metadata={"source": path.name, "title": title, "section": section}))
    return chunks


def list_policies() -> list[dict]:
    out = []
    for path in sorted(settings.POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        out.append({"name": path.name, "title": text.splitlines()[0].lstrip("# ").strip(), "content": text})
    return out


def employee_profile(emp) -> str:
    """The verified employee's record, written as text for the LLM."""
    return (f"Employee profile: {emp.name} ({emp.employee_code})\n"
            f"Department: {emp.department or '-'} | Designation: {emp.designation or '-'}\n"
            f"Access level: {emp.access_level} | Status: {emp.status}\n"
            f"Shift: {emp.shift or '-'} | Office: {emp.office_location or '-'} | Manager: {emp.manager or '-'}")
