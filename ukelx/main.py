from __future__ import annotations
import json
import polars as pl
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itertools import groupby
from operator import attrgetter

from .config import settings
from .jinja import templates
from .preprocessing import preprocess_data
from .models import ConstituencyDetail

app = FastAPI()

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Load cached constituencies
try:
    with open(static_dir / "cached_constituencies.json") as f:
        cached_constituencies = json.load(f)
    # Convert cached data to ConstituencyDetail objects
    cached_constituencies = [ConstituencyDetail(**constituency) for constituency in cached_constituencies]
except:
    cached_constituencies = []

# Preprocess live data (if available and needed)
try:
    uncached_ids = pl.DataFrame(cached_constituencies).filter(pl.col("status") != "result")["constituency_id"].unique().to_list()
except:
    uncached_ids = None
live_constituencies = preprocess_data(ids=uncached_ids)
live_ids = {c.constituency_id for c in live_constituencies}
constituencies = live_constituencies+[c for c in cached_constituencies if c.constituency_id not in live_ids]

def group_constituencies(constituencies):
    sorted_constituencies = sorted(constituencies, key=attrgetter('name'))
    grouped = []
    for name, group in groupby(sorted_constituencies, key=attrgetter('name')):
        results = list(group)
        results.sort(key=lambda x: x.vote_number, reverse=True)
        grouped.append({
            'name': name,
            'results': results
        })
    return grouped

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/constituencies", response_class=HTMLResponse)
async def get_constituencies(request: Request):
    grouped_constituencies = {}
    for constituency in constituencies:
        grouped_constituencies.setdefault(constituency.constituency_id, [])
        grouped_constituencies[constituency.constituency_id].append(constituency)
    return templates.TemplateResponse("components/constituencies_list.html", {"request": request, "constituencies": grouped_constituencies})

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
