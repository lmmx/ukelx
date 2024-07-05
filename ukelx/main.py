from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .preprocessing import preprocess_data
from .models import ConstituencyOverview, ConstituencyDetail

app = FastAPI()

constituencies = preprocess_data()


@app.get("/constituencies", response_model=list[ConstituencyOverview])
async def get_constituencies():
    return constituencies


@app.get("/constituency/{constituency_id}", response_model=ConstituencyDetail)
async def get_constituency(constituency_id: str):
    for constituency in constituencies:
        if constituency.constituency_id == constituency_id:
            return constituency
    raise HTTPException(status_code=404, detail="Constituency not found")


def serve():
    import uvicorn

    uvicorn.run("ukelx.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    serve()
