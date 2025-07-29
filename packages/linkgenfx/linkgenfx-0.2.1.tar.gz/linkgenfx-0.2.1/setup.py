from setuptools import setup, find_packages
from pathlib import Path

# Read README.md safely
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="linkgenfx",
    version="0.2.1",
    author="EFXTv",
    author_email="youremail@example.com",  # <-- Optional but recommended
    description="A simple script to create Serveo.net reverse tunnels",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/efxtv/linkgenfx",
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",   # <-- Recommended
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
        "Topic :: Internet",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "linkgenfx=linkgenfx.main:cli"
        ],
    },
    install_requires=[],  # Add dependencies here if needed
)

