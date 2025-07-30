import pkg_resources
import subprocess as sb
from pathlib import Path


def main():
    script_path = pkg_resources.resource_filename(
        __name__, "app.py"
    )

    sb.run(["streamlit", "run", script_path], check=True)


if __name__ == "__main__":
    print(Path("app.py"))