from setuptools import find_packages, setup

with open("README.md", "r") as readme:
    page_description = readme.read()

with open("requirements.txt") as req:
    requirements = req.read().splitlines()

setup(
    name="imgprocessdio",
    version="0.0.1",
    author="Caio Simonassi",
    author_email="iamcaiosimonassi@gmail.com",
    description="Image Processing package, compare and see diffences of histograsms between images",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Memlith/pacote-processamento-imagem.git",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
)
