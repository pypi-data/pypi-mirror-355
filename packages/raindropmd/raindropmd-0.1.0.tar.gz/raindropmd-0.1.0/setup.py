from setuptools import setup, find_packages

setup(
    name="raindropmd",
    version="0.1.0",
    description="Raindrop.io CSV to Zettelkasten Markdown CLI",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
        "jinja2"
    ],
    entry_points={
        "console_scripts": [
            "raindropmd=raindropmd.cli:main"
        ]
    },
    include_package_data=True,
)
