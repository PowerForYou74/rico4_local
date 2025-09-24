from fastapi import APIRouter, UploadFile, File, Form, Depends, Query
from sqlmodel import select
from .db import init_db, session
from .models import Prompt, PromptVersion, KBFile, KBChunk, Run, Setting
from .embed import chunk_and_embed
from .events import queue_event

router = APIRouter(prefix="/v2/core")

@router.on_event("startup")
def _startup():
    init_db()

# Prompts
@router.get("/prompts")
def list_prompts(s=Depends(session)):
    return s.exec(select(Prompt)).all()

@router.post("/prompts")
def create_prompt(name: str = Form(...), role: str = Form("system"), tags: str = Form(""), body: str = Form(...), s=Depends(session)):
    p = Prompt(name=name, role=role, tags=tags)
    s.add(p)
    s.commit()
    s.refresh(p)
    v = PromptVersion(prompt_id=p.id, body=body)
    s.add(v)
    s.commit()
    return {"id": p.id}

@router.get("/prompts/{pid}/versions")
def list_prompt_versions(pid: int, s=Depends(session)):
    return s.exec(select(PromptVersion).where(PromptVersion.prompt_id==pid).order_by(PromptVersion.id.desc())).all()

@router.post("/prompts/{pid}/versions")
def add_version(pid: int, body: str = Form(...), s=Depends(session)):
    v = PromptVersion(prompt_id=pid, body=body)
    s.add(v)
    s.commit()
    s.refresh(v)
    return {"id": v.id}

# KB Upload & ingest
@router.post("/kb/upload")
async def kb_upload(f: UploadFile = File(...), s=Depends(session)):
    path = f"uploads/{f.filename}"
    import os
    os.makedirs("uploads", exist_ok=True)
    open(path, "wb").write(await f.read())
    k = KBFile(name=f.filename, path=path, status="ingesting")
    s.add(k)
    s.commit()
    s.refresh(k)
    chunks = chunk_and_embed(path)  # returns list[str]
    for t in chunks:
        s.add(KBChunk(file_id=k.id, text=t))
    k.status = "ready"
    s.add(k)
    s.commit()
    return {"id": k.id}

@router.get("/kb/files")
def kb_files(s=Depends(session)):
    return s.exec(select(KBFile)).all()

@router.get("/kb/search")
def kb_search(q: str = Query(..., min_length=2), top: int = 5, s=Depends(session)):
    # simpler LIKE-Suchstub – später Embeddings ersetzen
    q_like = f"%{q}%"
    rows = s.exec(select(KBChunk).where(KBChunk.text.like(q_like)).limit(top)).all()
    out = []
    for r in rows:
        f = s.get(KBFile, r.file_id)
        out.append({"chunk_id": r.id, "file_id": r.file_id, "file": f.name if f else "?", "snippet": r.text[:400]})
    return out

# Runs/Telemetry (append-only)
@router.get("/runs")
def list_runs(s=Depends(session)):
    return s.exec(select(Run).order_by(Run.id.desc()).limit(200)).all()

@router.post("/runs")
def add_run(run: Run, s=Depends(session)):
    s.add(run)
    s.commit()
    return {"ok": True}

# Settings (flags only, keine Secrets)
@router.get("/settings")
def list_settings(s=Depends(session)):
    return s.exec(select(Setting)).all()

@router.post("/events")
def post_event(event: dict):
    return queue_event(event)
