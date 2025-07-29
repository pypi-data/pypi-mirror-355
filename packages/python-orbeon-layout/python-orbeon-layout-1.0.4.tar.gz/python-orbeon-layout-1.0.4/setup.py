from setuptools import setup, find_packages


setup(
    name="python-orbeon-layout",
    version="1.0.4",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "python_orbeon_layout": [
            "contents/fonts/*.OTF",
            "contents/fonts/*.otf",
        ],
    },
    description="Uma biblioteca simples e independente para geração de layouts padronizados em formato de imagem.",
    author="Edu Fontes",
    author_email="eduramofo@gmail.com",
    url="https://github.com/getorbeon/python-orbeon-layout",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
