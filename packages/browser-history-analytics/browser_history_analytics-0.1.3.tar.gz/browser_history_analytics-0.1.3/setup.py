from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="browser-history-analytics",
    version="0.1.3",
    author="Arpit Sengar (arpy8)",
    description="A package to visualize your browser history :D",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'browser_history_analytics': ['*.py'],
    },
    install_requires=[
        "streamlit", 
        "plotly", 
        "pandas", 
        "browser-history", 
        "numpy", 
        "seaborn", 
        "matplotlib", 
        "urllib3",
        "setuptools>=66.1.1",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "browser-history-analytics=browser_history_analytics.main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)