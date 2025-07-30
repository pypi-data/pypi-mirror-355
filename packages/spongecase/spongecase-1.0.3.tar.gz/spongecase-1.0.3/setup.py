from setuptools import setup

version = {}

with open("spongecase/__version__.py", "r") as f:
    exec(f.read(), version)

with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="spongecase",
    version=version["__version__"],
    description="Convert text to Spongebob case",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/nkouevda/spongecase",
    author="Nikita Kouevda",
    author_email="nkouevda@gmail.com",
    license="MIT",
    packages=["spongecase"],
    entry_points={
        "console_scripts": [
            "spongecase=spongecase.__main__:main",
        ],
    },
)
