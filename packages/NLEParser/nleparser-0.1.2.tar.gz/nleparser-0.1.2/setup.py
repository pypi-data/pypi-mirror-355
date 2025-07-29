from setuptools import setup, find_packages

setup(
    name="NLEParser",
    version="0.1.2",
    author="NateLang",
    author_email="natancorreiatr@gmail.com",
    description="A Natural language processing parser for Zork-style games",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
)
