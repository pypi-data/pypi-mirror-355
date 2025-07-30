from setuptools import setup, find_packages

setup(  
    name="flaubert-image-processing", 
    version="0.1.0",
    description="Pacote de processamento de imagens em Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Flaubert Caldeira da Silva Junior",
    author_email="flaubertweb@gmail.com",
    url="https://github.com/FlaubertWeb/image-processing-package",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "scikit-image",
        "matplotlib",
        "numpy",
        "setuptools"
    ],
    python_requires=">=3.7",
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
