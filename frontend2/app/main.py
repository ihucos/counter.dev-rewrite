from js import window, document
from pathlib import Path


def main():
    page = Path(document.location.pathname).name.split(".")[0]
    __import__(f"pages.{page}")
