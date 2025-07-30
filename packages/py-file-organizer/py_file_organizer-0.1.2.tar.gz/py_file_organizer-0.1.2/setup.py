from setuptools import setup, find_packages

setup(
    name="py_file_organizer",
    version="0.1.2",
    description="A simple tool to organize files into folders by type. To use as a CLI tool, use the command 'file-organizer' ",
    author="Oteri Eyenike",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "file-organizer=file_organizer.cli:main"
        ]
    },
    python_requires=">=3.6",
) 
