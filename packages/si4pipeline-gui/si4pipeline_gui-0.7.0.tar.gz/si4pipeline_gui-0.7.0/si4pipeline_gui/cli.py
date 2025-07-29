import sys
from importlib import resources
from streamlit.web.cli import main as _st_run

def main() -> None:
    with resources.as_file(resources.files("si4pipeline_gui") / "app.py") as path:
        sys.argv = ["streamlit", "run", str(path), *sys.argv[1:]]
        _st_run()
