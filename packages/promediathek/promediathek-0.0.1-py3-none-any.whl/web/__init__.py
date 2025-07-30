from flask import Flask
from .webtmpdir import WebTmpDir

app = Flask(__name__)
web_dirs: list[WebTmpDir] = []
