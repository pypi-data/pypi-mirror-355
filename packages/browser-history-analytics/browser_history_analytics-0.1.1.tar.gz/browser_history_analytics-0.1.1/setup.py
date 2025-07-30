from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="browser-history-analytics",
    version="0.1.1",
    author="Arpit Sengar (arpy8)",
    description="A package to visualize your browser history :D",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
                        "streamlit", 
                        "plotly", 
                        "pandas", 
                        "browser-history", 
                        "numpy", 
                        "seaborn", 
                        "matplotlib", 
                        "urllib3",
                        "setuptools==66.1.1"
                    ],
    entry_points={
        "console_scripts": [
            "browser_history_analytics=browser_history_analytics.main:main",
        ],
    }
)