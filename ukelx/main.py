from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itertools import groupby
from operator import attrgetter

from .config import settings
from .preprocessing import preprocess_data
from .models import ConstituencyDetail

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

constituencies = preprocess_data()

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
    grouped_constituencies = group_constituencies(constituencies)
    return templates.TemplateResponse("constituencies_list.html", {"request": request, "constituencies": grouped_constituencies})

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
