
from setuptools import setup, find_packages

setup(
    name="modelcli",
    version="0.1.0",
    author="Tomás Gambirassi",
    author_email="tomasgambirassi@gmail.com",
    description="Universal CLI for sending prompts to any LLM model and provider.",
    long_description="See GitHub for usage.",
    url="https://github.com/Tomigambii/modelcli",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "modelcli = modelcli.cli:run"
        ]
    },
)
