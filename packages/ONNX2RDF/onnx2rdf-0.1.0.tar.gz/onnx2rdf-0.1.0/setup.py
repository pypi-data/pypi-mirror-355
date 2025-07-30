from setuptools import setup
from setuptools.command.install import install
import urllib.request
from pathlib import Path

JAR_URL = "https://github.com/RMLio/rmlmapper-java/releases/download/v7.3.3/rmlmapper-7.3.3-r374-all.jar"
JAR_PATH = Path(__file__).parent / "ONNX2RDF" / "rmlmapper.jar"

class CustomInstall(install):
    def run(self):
        install.run(self)
        if not JAR_PATH.exists():
            print(f"Downloading JAR from {JAR_URL}")
            JAR_PATH.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(JAR_URL, JAR_PATH)

setup(cmdclass={"install": CustomInstall})