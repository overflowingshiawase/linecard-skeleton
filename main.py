from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}
from pydantic import BaseModel, EmailStr

class CardCreateSchema(BaseModel):
    slug: str
    name: str
    title: str | None = None
    company: str | None = None
    phone: str | None = None
    email: EmailStr | None = None

@app.post("/api/cards")
def create_card(card: CardCreateSchema):
    data = card.dict()
    response = supabase.table("cards").upsert(data, on_conflict="slug").execute()
    return {"success": True, "data": response.data}

from fastapi import UploadFile, File
import uuid

@app.post("/api/upload")
async def upload_photo(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    file_path = f"{uuid.uuid4()}.{ext}"
    content = await file.read()
    supabase.storage.from_("avatars").upload(file_path, content)
    public_url = supabase.storage.from_("avatars").get_public_url(file_path)
    return {"url": public_url}

from fastapi.responses import HTMLResponse
from fastapi import HTTPException

@app.get("/card/{slug}", response_class=HTMLResponse)
def view_card(slug: str):
    res = supabase.table("cards").select("*").eq("slug", slug).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="找不到這張名片")
    c = res.data[0]
    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h1>{c.get('name')}</h1>
        <p>{c.get('title') or ''} @ {c.get('company') or ''}</p>
        <p>{c.get('phone') or ''} | {c.get('email') or ''}</p>
        <a href="https://social-plugins.line.me/lineit/share?url=http://localhost:8000/card/{slug}">
            <button>分享到LINE</button>
        </a>
    </body></html>
    """