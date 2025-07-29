from setuptools import setup, find_packages

setup(
    name="lyrically",
    version="1.0.1",
    description="A Python library for scraping song lyrics",
    author="Filming",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=["aiohttp", "aiosqlite", "beautifulsoup4", "lxml"],
)
