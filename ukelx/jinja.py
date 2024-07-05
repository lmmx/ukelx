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
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

# Add the custom filter to the Jinja2 environment
templates.env.filters['datetime'] = datetime_filter
