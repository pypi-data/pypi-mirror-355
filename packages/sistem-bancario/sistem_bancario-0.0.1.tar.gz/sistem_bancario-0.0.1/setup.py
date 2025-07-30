from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="sistem_bancario",
    version="0.0.1",
    author="Beatriz",
    description="Sistema Bancário simples utilizando Python",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Beiatrixx/sistema-bancario-package",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "sistem-bancario=sistem_bancario.banco:main"
        ]
    }
)