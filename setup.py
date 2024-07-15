from setuptools import setup

# try to load version from generated VERSION file
try:
    with open("VERSION", "r", encoding="utf-8") as f:
        version = f.read()
except FileNotFoundError:
    version = None  # fallback to setup.cfg

setup(version=version)
