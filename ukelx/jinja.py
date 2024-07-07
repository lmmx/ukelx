from pathlib import Path
from fastapi.templating import Jinja2Templates

__all__ = ["templates"]

template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=template_dir)


# Custom filter for datetime formatting
def datetime_filter(timestamp):
    from datetime import datetime

    if timestamp is None:
        return "Not available"
    return (
        datetime.fromtimestamp(timestamp / 1000).strftime("%I:%M%p").lstrip("0").lower()
    )


def stacked_bar_sort_candidates(candidates, sorted_parties):
    sorted_parties = list(sorted_parties)
    # print(f"Got {sorted_parties=}")
    def party_sorter(candidate) -> int:
        party = candidate.party_code
        if party in sorted_parties:
            idx = sorted_parties.index(party)
        else:
            idx = len(sorted_parties)
        return idx

    sorted_data = sorted(candidates, key=party_sorter)
    print([c.party_code for c in sorted_data])
    return sorted_data


# Add the custom filter to the Jinja2 environment
templates.env.filters["datetime"] = datetime_filter
templates.env.filters["sort_candidates"] = stacked_bar_sort_candidates
