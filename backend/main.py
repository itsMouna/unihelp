from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time, os, json, jwt, hashlib, re

from llm import get_answer, generate_email, stream_answer
from rag import ingest_document, get_context

# ── Config ─────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "unihelp-secret-2025")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 8

app = FastAPI(title="UniHelp API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ── Rate limiter ───────────────────────────────────────────────────────────────
_rate_store: dict = defaultdict(list)

def rate_limit(ip: str, max_req: int = 20, window: int = 60):
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < window]
    if len(_rate_store[ip]) >= max_req:
        raise HTTPException(429, f"Trop de requêtes. Max {max_req}/{window}s.")
    _rate_store[ip].append(now)

def client_ip(req: Request) -> str:
    fwd = req.headers.get("X-Forwarded-For")
    return fwd.split(",")[0] if fwd else req.client.host

# ── Users (demo — replace with real DB) ───────────────────────────────────────
USERS = {
    "etudiant": {"password_hash": hashlib.sha256(b"iit2025").hexdigest(),  "role": "student", "name": "Étudiant IIT"},
    "admin":    {"password_hash": hashlib.sha256(b"admin2025").hexdigest(), "role": "admin",   "name": "Administrateur"},
}

# ── JWT ────────────────────────────────────────────────────────────────────────
def create_token(data: dict) -> str:
    p = {**data, "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(p, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expiré. Reconnectez-vous.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token invalide.")

def require_admin(user: dict = Depends(verify_token)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Accès réservé aux administrateurs.")
    return user

# ── Input sanitizer ────────────────────────────────────────────────────────────
def sanitize(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()

# ── Models ─────────────────────────────────────────────────────────────────────
class HistoryMsg(BaseModel):
    role: str
    content: str

    @validator("role")
    def valid_role(cls, v):
        assert v in ("user", "assistant"), "Invalid role"
        return v

    @validator("content")
    def limit_content(cls, v):
        return v.strip()[:2000]

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMsg] = []

    @validator("message")
    def valid_message(cls, v):
        v = sanitize(v.strip())
        assert v, "Message vide"
        assert len(v) <= 1000, "Message trop long (max 1000 caractères)"
        return v

    @validator("history")
    def limit_history(cls, v):
        return v[-10:]

class EmailRequest(BaseModel):
    email_type: str
    student_name: Optional[str] = ""
    reason: Optional[str] = ""

    @validator("email_type")
    def valid_type(cls, v):
        allowed = [
            "Demande d'attestation de scolarité", "Demande de stage PFE",
            "Réclamation de note", "Justification d'absence",
            "Demande de transfert", "Demande de bourse",
        ]
        assert v in allowed, f"Type invalide. Acceptés: {allowed}"
        return v

    @validator("student_name", "reason")
    def clean(cls, v):
        return sanitize(v)[:200] if v else ""

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "UniHelp API is running 🎓", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# AUTH
@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    rate_limit(client_ip(request), max_req=5, window=60)
    user = USERS.get(form.username)
    if not user or hashlib.sha256(form.password.encode()).hexdigest() != user["password_hash"]:
        raise HTTPException(401, "Identifiants incorrects.")
    token = create_token({"sub": form.username, "role": user["role"], "name": user["name"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"], "name": user["name"]}

@app.get("/auth/me")
def me(user: dict = Depends(verify_token)):
    return {"username": user["sub"], "role": user["role"], "name": user["name"]}

# CHAT
@app.post("/chat")
async def chat(body: ChatRequest, request: Request, user: dict = Depends(verify_token)):
    rate_limit(client_ip(request), max_req=30, window=60)
    try:
        context  = get_context(body.message)
        response = get_answer(body.message, context, body.history)
        return {"response": response, "has_context": bool(context)}
    except Exception as e:
        raise HTTPException(500, f"Erreur LLM: {e}")

@app.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request, user: dict = Depends(verify_token)):
    rate_limit(client_ip(request), max_req=20, window=60)
    context = get_context(body.message)

    def generate():
        try:
            for chunk in stream_answer(body.message, context, body.history):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# EMAIL
@app.post("/email")
async def email(body: EmailRequest, request: Request, user: dict = Depends(verify_token)):
    rate_limit(client_ip(request), max_req=10, window=60)
    try:
        return {"email": generate_email(body.email_type, body.student_name, body.reason)}
    except Exception as e:
        raise HTTPException(500, str(e))

# DOCUMENTS
@app.post("/upload")
async def upload(file: UploadFile = File(...), request: Request = None, user: dict = Depends(require_admin)):
    rate_limit(client_ip(request), max_req=10, window=60)
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Seuls les fichiers PDF sont acceptés.")
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(400, "Fichier trop volumineux (max 20 MB).")
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
    os.makedirs("./docs", exist_ok=True)
    path = f"./docs/{safe_name}"
    with open(path, "wb") as f:
        f.write(contents)
    try:
        count = ingest_document(path)
        return {"message": "✅ Document indexé", "chunks": count, "filename": safe_name,
                "size_kb": round(len(contents) / 1024, 1)}
    except Exception as e:
        os.remove(path)
        raise HTTPException(500, f"Erreur d'indexation: {e}")

@app.get("/documents")
def list_docs(user: dict = Depends(verify_token)):
    path = "./docs"
    if not os.path.exists(path):
        return {"documents": [], "total": 0}
    files = [f for f in os.listdir(path) if f.endswith(".pdf")]
    return {"documents": [{"name": f, "status": "Indexé",
                            "size_kb": round(os.path.getsize(f"./docs/{f}") / 1024, 1)}
                           for f in files], "total": len(files)}

@app.delete("/documents/{filename}")
def delete_doc(filename: str, user: dict = Depends(require_admin)):
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    path = f"./docs/{safe}"
    if not os.path.exists(path):
        raise HTTPException(404, "Document introuvable.")
    os.remove(path)
    return {"message": f"✅ Supprimé: {safe}"}