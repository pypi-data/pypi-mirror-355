from setuptools import setup, find_packages

setup(
    name="py_file_organizer",
    version="0.1.1",
    description="A simple tool to organize files into folders by type.",
    author="Oteri Eyenike",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "py_file_organizer=file_organizer.cli:main",
            "file-organizer=file_organizer.cli:main"
        ]
    },
    python_requires=">=3.6",
) 
