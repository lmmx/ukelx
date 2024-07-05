import asyncio

import httpx
from httpx import RequestError, HTTPStatusError
import polars as pl

from .config import CONSTITUENCIES_OVERVIEW_URL, CONSTITUENCY_DETAIL_URL_TEMPLATE
from .models import ConstituencyDetail


async def fetch_json(client, url, max_retries=3):
    print(f"Fetching {url}")
    for attempt in range(max_retries):
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except (RequestError, HTTPStatusError) as exc:
            print(f"Error fetching {url}: {exc}")
            if attempt < max_retries - 1:
                print(f"Retrying ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(2**attempt)  # Exponential backoff
            else:
                print(f"Failed to fetch {url} after {max_retries} attempts.")
                return None


async def fetch_all_details(constituency_ids):
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_json(client, CONSTITUENCY_DETAIL_URL_TEMPLATE.format(constituency_id))
            for constituency_id in constituency_ids
        ]
        return await asyncio.gather(*tasks)


def sync_fetch_json(url: str) -> dict:
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def preprocess_data():
    # Fetch and process constituencies overview
    overview_data = sync_fetch_json(CONSTITUENCIES_OVERVIEW_URL)
    flat_data = (
        {**data, "constituency_id": constituency_id}
        for constituency_id, data in overview_data.items()
    )
    overview_df = pl.DataFrame(flat_data)

    # Fetch and process constituency details
    constituency_ids = overview_df["constituency_id"].to_list()
    details_data = asyncio.run(fetch_all_details(constituency_ids))
    breakpoint()
    details_df = pl.DataFrame(details_data)

    # Merge overview and details data
    merged_df = overview_df.join(details_df, on="constituency_id", how="left")

    # Convert to Pydantic models
    constituencies = [ConstituencyDetail(**row) for row in merged_df.to_dicts()]

    return constituencies


if __name__ == "__main__":
    preprocessed_data = preprocess_data()
    print(f"Preprocessed {len(preprocessed_data)} constituencies")
