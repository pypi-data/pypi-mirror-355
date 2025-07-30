import os
import warnings
import pkg_resources
import subprocess as sb
from console import print_content, PORT

warnings.filterwarnings("ignore")


def main():
    script_path = pkg_resources.resource_filename(__name__, "app.py")
    print_content()

    with open(os.devnull, 'w') as fnull:
        sb.run(["streamlit", "run", script_path, "--server.port", PORT], check=True, stdout=fnull, stderr=fnull)
    
if __name__ == "__main__":
    main()