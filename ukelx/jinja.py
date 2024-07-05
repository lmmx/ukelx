from pathlib import Path
from fastapi.templating import Jinja2Templates

__all__ = ["templates"]

template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=template_dir)
