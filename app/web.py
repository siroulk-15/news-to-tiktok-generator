"""Minimal local web interface for editorial review."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.database import ScriptDraftDB, close_db, get_db, init_db
from app.services.workflow import EditorialWorkflow

app = FastAPI(title="NTG Review", docs_url=None, redoc_url=None, openapi_url=None)


PAGE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NTG | Revue éditoriale</title>
  <style>
    :root { --ink:#17221f; --muted:#66736e; --paper:#f5f1e8; --panel:#fffdf8; --line:#d8d4c9; --accent:#d45d38; --ok:#287a5b; }
    * { box-sizing:border-box; } body { margin:0; color:var(--ink); background:var(--paper); font-family:Georgia, 'Times New Roman', serif; }
    header { padding:32px 6vw 22px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:20px; align-items:end; }
    h1 { margin:0; font-size:clamp(2rem,5vw,4.2rem); line-height:.95; font-weight:500; letter-spacing:0; } header p { margin:0; color:var(--muted); font:14px/1.4 system-ui,sans-serif; max-width:320px; }
    main { width:min(1180px,88vw); margin:34px auto 70px; } .toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; gap:12px; }
    .count { font:600 13px system-ui,sans-serif; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); } button { border:0; padding:11px 16px; cursor:pointer; font:600 13px system-ui,sans-serif; border-radius:4px; }
    .refresh { background:var(--ink); color:white; } .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); gap:16px; }
    article { background:var(--panel); border:1px solid var(--line); padding:22px; display:flex; flex-direction:column; min-height:265px; } article h2 { font-size:1.35rem; font-weight:500; line-height:1.1; margin:13px 0 12px; }
    .meta { display:flex; gap:8px; flex-wrap:wrap; font:11px system-ui,sans-serif; color:var(--muted); } .badge { color:var(--accent); font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
    .summary { color:#4c5853; line-height:1.45; margin:0 0 16px; } .draft { border-top:1px solid var(--line); padding-top:14px; margin-bottom:18px; } .draft-label { font:700 10px system-ui,sans-serif; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); } .draft p { white-space:pre-line; font:13px/1.5 system-ui,sans-serif; margin:7px 0 0; color:#33413c; } .actions { margin-top:auto; display:flex; gap:8px; } .approve { background:var(--ok); color:#fff; } .reject { background:#eadfd9; color:#7d3424; }
    .empty { border:1px dashed var(--line); padding:50px 20px; text-align:center; color:var(--muted); grid-column:1/-1; } .error { color:#9d2c1d; font:14px system-ui,sans-serif; }
  </style>
</head>
<body>
  <header><h1>Revue<br>éditoriale</h1><p>NTG · Les brouillons restent locaux et nécessitent une décision humaine avant toute automatisation.</p></header>
  <main><div class="toolbar"><span id="count" class="count">Chargement...</span><button class="refresh" onclick="loadQueue()">Actualiser</button></div><section id="grid" class="grid"></section></main>
  <script>
    const grid = document.getElementById('grid'), count = document.getElementById('count');
    const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    async function loadQueue() {
      try { const response = await fetch('/api/review'); if (!response.ok) throw new Error('Impossible de charger la file'); const items = await response.json();
        count.textContent = `${items.length} story${items.length > 1 ? 's' : ''} en attente`;
        grid.innerHTML = items.length ? items.map(item => `<article><div class="meta"><span class="badge">${esc(item.status)}</span><span>${item.source_count} source${item.source_count > 1 ? 's' : ''}</span><span>Insolite ${Number(item.insolite_score ?? 0).toFixed(2)}</span></div><h2>${esc(item.title)}</h2><p class="summary">${esc(item.summary)}</p><div class="draft"><span class="draft-label">Brouillon</span><p>${esc(item.draft_text || 'Aucun brouillon disponible.')}</p></div><div class="actions"><button class="approve" onclick="decide('${esc(item.id)}','approve')">Approuver</button><button class="reject" onclick="decide('${esc(item.id)}','reject')">Rejeter</button></div></article>`).join('') : '<div class="empty">Aucune story en attente de revue.</div>';
      } catch (error) { count.textContent = ''; grid.innerHTML = `<div class="empty error">${esc(error.message)}</div>`; }
    }
    async function decide(id, action) { const response = await fetch(`/api/${action}/${encodeURIComponent(id)}`, {method:'POST'}); if (!response.ok) { const data = await response.json(); alert(data.detail || 'Action impossible'); return; } loadQueue(); }
    loadQueue();
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the local editorial review page."""
    return PAGE


@app.get("/api/review")
def review_queue() -> list[dict]:
    """Return selected stories for the review UI."""
    init_db()
    db = get_db()
    try:
        items = []
        for story in EditorialWorkflow(db).review_queue(limit=100):
            draft = db.query(ScriptDraftDB).filter(
                ScriptDraftDB.story_id == story.id
            ).first()
            items.append({
                "id": story.id,
                "title": story.title,
                "summary": story.summary,
                "status": story.status,
                "source_count": story.source_count,
                "insolite_score": story.insolite_score,
                "confidence_score": story.confidence_score,
                "draft_text": draft.draft_text if draft else None,
            })
        return items
    finally:
        close_db(db)


def _decide(story_id: str, action: str) -> dict:
    init_db()
    db = get_db()
    try:
        workflow = EditorialWorkflow(db)
        story = workflow.approve(story_id) if action == "approve" else workflow.reject(story_id)
        return {"id": story.id, "status": story.status}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    finally:
        close_db(db)


@app.post("/api/approve/{story_id}")
def approve(story_id: str) -> dict:
    return _decide(story_id, "approve")


@app.post("/api/reject/{story_id}")
def reject(story_id: str) -> dict:
    return _decide(story_id, "reject")