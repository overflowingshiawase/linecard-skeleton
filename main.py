from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import uuid

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

BASE_URL = "https://web-production-4fe72.up.railway.app"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CardCreateSchema(BaseModel):
    slug: str
    name: str
    title: str | None = None
    company: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/form")
def form_page():
    return FileResponse("form.html")


@app.post("/api/cards")
def create_card(card: CardCreateSchema):
    data = card.dict()
    response = supabase.table("cards").upsert(data, on_conflict="slug").execute()
    return {"success": True, "data": response.data}


@app.post("/api/upload")
async def upload_photo(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    file_path = f"{uuid.uuid4()}.{ext}"
    content = await file.read()
    supabase.storage.from_("avatars").upload(file_path, content)
    public_url = supabase.storage.from_("avatars").get_public_url(file_path)
    return {"url": public_url}


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
        <a href="https://social-plugins.line.me/lineit/share?url={BASE_URL}/card/{slug}">
            <button>分享到LINE</button>
        </a>
    </body></html>
    """