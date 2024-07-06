from __future__ import annotations
import json
import polars as pl
from pathlib import Path
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import TypeAdapter
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
    const_ta = TypeAdapter(list[ConstituencyDetail])
    cached_constituencies = const_ta.validate_python(cached_constituencies)
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

# Define party colors
party_colors = {
    'LAB': '#d60000',
    'CON': '#0099db',
    'LD': '#faa61a',
    'GRN': '#33a22b',
    'SNP': '#fff95d',
    'REF': '#12B6CF',
    'IND': '#CCCCCC',
    'SF': '#005717',
    'DUP': '#D46A4C',
    'PC': '#008142',
    'SDLP': '#69C1BD',
    'OTH': '#929292',
    'APNI': '#F6CB2F',
    'UUP': '#48A5EE',
    'SPK': '#7D827E',
    'UKIP': '#70147A'
}

templates.env.globals['party_colors'] = party_colors

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

def sort_constituencies(constituencies, sort_by):
    if sort_by == "name":
        return sorted(constituencies, key=lambda x: x[0].name)
    elif sort_by == "majority":
        return sorted(constituencies, key=lambda x: x[0].majority_2024_percent or 0, reverse=True)
    elif sort_by == "swing":
        return sorted(constituencies, key=lambda x: abs((x[0].majority_2024_percent or 0) - (x[0].majority_2019_percent or 0)), reverse=True)
    elif sort_by == "runner_up_margin":
        return sorted(constituencies, key=lambda x: (x[0].vote_number or 0) - (x[1].vote_number or 0) if len(x) > 1 else float('inf'))
    else:
        return constituencies

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/constituencies", response_class=HTMLResponse)
async def get_constituencies(
    request: Request, 
    search: str = "", 
    parties: str = "", 
    regions: str = "", 
    sort: str = Query("name", enum=["name", "majority", "swing", "runner_up_margin"])
):
    filtered_constituencies = constituencies

    if search:
        filtered_constituencies = [c for c in filtered_constituencies if search.lower() in c.name.lower()]
    
    if parties:
        party_list = parties.split(',')
        filtered_constituencies = [c for c in filtered_constituencies if c.result_2024 in party_list]
    
    if regions:
        region_list = regions.split(',')
        filtered_constituencies = [c for c in filtered_constituencies if c.region in region_list]

    grouped_constituencies = {}
    for constituency in filtered_constituencies:
        grouped_constituencies.setdefault(constituency.constituency_id, [])
        grouped_constituencies[constituency.constituency_id].append(constituency)
    
    sorted_constituencies = sort_constituencies(grouped_constituencies.values(), sort)
    
    # Calculate summary
    summary = defaultdict(lambda: {'seats': 0, 'votes': 0})
    total_votes = 0
    for constituency_group in sorted_constituencies:
        winning_party = constituency_group[0].result_2024
        if winning_party:
            summary[winning_party]['seats'] += 1
        for candidate in constituency_group:
            if candidate.vote_number:
                summary[candidate.party_code]['votes'] += candidate.vote_number
                total_votes += candidate.vote_number
    
    for party in summary:
        summary[party]['vote_share'] = (summary[party]['votes'] / total_votes) * 100 if total_votes > 0 else 0
    
    summary = dict(sorted(summary.items(), key=lambda x: x[1]['seats'], reverse=True))
    
    return templates.TemplateResponse(
        "components/constituencies_list.html", 
        {
            "request": request, 
            "constituencies": {c[0].constituency_id: c for c in sorted_constituencies},
            "summary": summary,
            "party_colors": party_colors
        }
    )

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
