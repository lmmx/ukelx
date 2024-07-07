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


def stacked_bar_sort_candidates(
    candidates, sorted_parties, party_antisort=None, party_sort=None
):
    sorted_parties = list(sorted_parties)

    # Move the anti-sort party to the end
    if party_antisort and party_antisort in sorted_parties:
        sorted_parties.append(sorted_parties.pop(sorted_parties.index(party_antisort)))

    # Move the sort-by party to the beginning
    if party_sort and party_sort in sorted_parties:
        sorted_parties.insert(0, sorted_parties.pop(sorted_parties.index(party_sort)))

    def party_sorter(candidate) -> int:
        party = candidate.party_code
        if party in sorted_parties:
            idx = sorted_parties.index(party)
        else:
            idx = len(sorted_parties)
        return idx

    sorted_data = sorted(candidates, key=party_sorter)
    return sorted_data


# Add the custom filter to the Jinja2 environment
templates.env.filters["datetime"] = datetime_filter
templates.env.filters["sort_candidates"] = stacked_bar_sort_candidates
