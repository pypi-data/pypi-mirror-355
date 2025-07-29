from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="mumobo",
    use_scm_version=True,
    setup_requires=["setuptools-scm"],
    description="API for the mumobo device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Maurice Friedrichs",
    author_email="huberse@phys.ethz.ch",
    url="https://gitlab.phys.ethz.ch/code/experiment/mumobo",
    packages=find_packages(include=["mumobo", "mumobo.*"]),
    python_requires=">=3.8",
)