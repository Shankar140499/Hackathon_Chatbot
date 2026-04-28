from pathlib import Path
import runpy


STREAMLIT_APP = Path(__file__).resolve().parent / "VSC" / "app.py"


if __name__ == "__main__":
    runpy.run_path(str(STREAMLIT_APP), run_name="__main__")
