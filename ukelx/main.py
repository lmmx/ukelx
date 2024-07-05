from __future__ import annotations
import json
import polars as pl
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .jinja import templates
from .preprocessing import preprocess_data
from .models import ConstituencyDetail

app = FastAPI()

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Load cached constituencies
with open(static_dir / "cached_constituencies.json") as f:
    cached_constituencies = json.load(f)

# Convert cached data to ConstituencyDetail objects
cached_constituencies = [ConstituencyDetail(**constituency) for constituency in cached_constituencies]

# Preprocess live data (if available and needed)
uncached_ids = pl.DataFrame(cached_constituencies).filter(pl.col("status") != "result")["constituency_id"].unique().to_list()
live_constituencies = preprocess_data(ids=uncached_ids)

def merge_constituencies(cached: list[ConstituencyDetail], live: list[ConstituencyDetail]) -> list[ConstituencyDetail]:
    merged = {c.constituency_id: c for c in cached}
    for constituency in live:
        if constituency.status == "result" or constituency.constituency_id not in merged:
            merged[constituency.constituency_id] = constituency
    return list(merged.values())

# Merge cached and live data
try:
    constituencies = merge_constituencies(cached_constituencies, live_constituencies)
except:
    constituencies = cached_constituencies

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    context = {"request": request, "settings": settings}
    return templates.TemplateResponse("index.html", context)

@app.get("/constituencies", response_class=HTMLResponse)
async def get_constituencies(request: Request):
    return templates.TemplateResponse("components/constituencies_list.html", {"request": request, "constituencies": constituencies})

@app.get("/constituencies_json", response_model=list[ConstituencyDetail])
async def get_constituencies_json():
    return constituencies

@app.get("/constituency/{constituency_id}", response_model=ConstituencyDetail)
async def get_constituency(constituency_id: str):
    for constituency in constituencies:
        if constituency.constituency_id == constituency_id:
            return constituency
    raise HTTPException(status_code=404, detail="Constituency not found")

def serve():
    import uvicorn

    uvicorn.run("ukelx.main:app", host="0.0.0.0", port=8000, reload=settings.reload)

if __name__ == "__main__":
    serve()
