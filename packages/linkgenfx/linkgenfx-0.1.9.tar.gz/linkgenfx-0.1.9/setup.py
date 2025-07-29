from setuptools import setup, find_packages

setup(
    name="linkgenfx",
    version="0.1.9",
    author="EFXTv",
    description="A simple script to create Serveo.net reverse tunnels",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/linkgenfx",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "linkgenfx=linkgenfx.main:cli"
        ],
    },
)
