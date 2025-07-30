from setuptools import setup, find_packages

setup(
    name="rastgelekelime",
    version="10.0.0",
    description="Bir yada daha fazla Türkçe kelime çıktısı alın.",
    author="Enes Kerem AYDIN",
    url="https://github.com/EnesKeremAYDIN/pip-rastgelekelime",
    packages=find_packages(),
    package_data={
        "rastgelekelime": ["data/wordList.json"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
