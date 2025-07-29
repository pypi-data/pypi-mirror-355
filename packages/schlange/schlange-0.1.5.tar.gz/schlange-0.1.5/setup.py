from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="schlange",
    version="0.1.5",
    author="Konja Rehm",
    description="Python auf Deutsch - Deutsche Schlüsselwörter für Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/schlange",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: German",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "schlange=schlange.cli:main",
        ],
    },
)
