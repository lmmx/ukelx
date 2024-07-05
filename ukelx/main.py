from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .config import settings
from .jinja import templates
from .preprocessing import preprocess_data
from .models import ConstituencyDetail

app = FastAPI()

constituencies = preprocess_data()


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
