
from setuptools import setup, find_packages

setup(
    name="modelcli",
    version="0.0.7",
    author="Tomás Gambirassi",
    author_email="tomasgambirassi@gmail.com",
    description="Universal CLI for sending prompts to any LLM model and provider.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Tomigambii/modelcli",
    project_urls={
        "Bug Tracker": "https://github.com/Tomigambii/modelcli/issues",
        "Source Code": "https://github.com/Tomigambii/modelcli"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "modelcli = modelcli.cli:run"
        ]
    },
)
