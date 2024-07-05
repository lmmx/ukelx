from fastapi.templating import Jinja2Templates

__all__ = ["templates"]

templates = Jinja2Templates(directory="gpx/templates")
