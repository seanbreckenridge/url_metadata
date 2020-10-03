import io
from setuptools import setup, find_packages

requirements = [
    "appdirs>=1.4.4",
    "lassie>=0.11.7",
    "readability-lxml>=0.8.1",
    "backoff>=1.10.0",
    "beautifulsoup4>=4.9.2",
    "click>=7.1.2",
    "logzero",
]

# Use the README.md content for the long description:
with io.open("README.md", encoding="utf-8") as fo:
    long_description = fo.read()

setup(
    name="url_metadata",
    version="0.1.0",
    url="https://github.com/seanbreckenridge/url_metadata",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=("""cache metadata from URLs"""),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=find_packages("src"),
    zip_safe=False,
    package_dir={"": "src"},
    install_requires=requirements,
    keywords="url cache data youtube subtitles",
    entry_points={
        "console_scripts": [
            "url_metadata = url_metadata.__main__:main",
        ]
    },
    classifiers=[
        "OSI Approved :: Apache Software License",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
