from pathlib import Path
import runpy
import sys


ROOT_DIR = Path(__file__).resolve().parent
APP_DIR = ROOT_DIR / "VSC"
STREAMLIT_APP = APP_DIR / "app.py"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


if __name__ == "__main__":
    runpy.run_path(str(STREAMLIT_APP), run_name="__main__")
