import polars as pl
import httpx

from .config import CONSTITUENCIES_OVERVIEW_URL, CONSTITUENCY_DETAIL_URL_TEMPLATE
from .models import ConstituencyDetail


def fetch_json(url: str) -> dict:
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def preprocess_data():
    # Fetch and process constituencies overview
    overview_data = fetch_json(CONSTITUENCIES_OVERVIEW_URL)
    overview_df = pl.DataFrame(overview_data)

    # Fetch and process constituency details
    details_data = []
    for constituency_id in overview_df["constituency_id"]:
        detail_url = CONSTITUENCY_DETAIL_URL_TEMPLATE.format(constituency_id)
        detail_data = fetch_json(detail_url)
        details_data.append(detail_data)

    details_df = pl.DataFrame(details_data)

    # Merge overview and details data
    merged_df = overview_df.join(details_df, on="constituency_id", how="left")

    # Convert to Pydantic models
    constituencies = [ConstituencyDetail(**row) for row in merged_df.to_dicts()]

    return constituencies


if __name__ == "__main__":
    preprocessed_data = preprocess_data()
    print(f"Preprocessed {len(preprocessed_data)} constituencies")
