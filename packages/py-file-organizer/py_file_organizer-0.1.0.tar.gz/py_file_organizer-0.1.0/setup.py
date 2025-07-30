from setuptools import setup, find_packages

setup(
    name="py_file_organizer",
    version="0.1.0",
    description="A simple tool to organize files into folders by type.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "file-organizer=file_organizer.cli:main"
        ]
    },
    python_requires=">=3.6",
) 
