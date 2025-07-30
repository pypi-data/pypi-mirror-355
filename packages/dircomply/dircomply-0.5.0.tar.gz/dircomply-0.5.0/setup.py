from setuptools import setup, find_packages

# Dynamically read the version from __init__.py
def get_version():
    version = {}
    with open("dircomply/version.py") as f:
        exec(f.read(), version)
    return version["__version__"]
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()
with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    changelog = f.read()
##########################

setup(
    name="dircomply",                 # Name of your package
    version=get_version(),            # Version of your package
    description="A small package to compare the files between two project folders.",  # Short description
    long_description=readme + "\n\n" + changelog,  # Append Changelog
    long_description_content_type="text/markdown",
    author="Benevant Mathew",
    author_email="benevantmathewv@gmail.com",
    license="MIT",                     # License type
    packages=find_packages(include=["dircomply"]),  # Include only 'dircomply' directory
    package_data={
        "dircomply": ["config/extensions.json"],  # Include the JSON file
    },
    include_package_data=True,
    install_requires=[],               # Add dependencies here
    entry_points={
        "console_scripts": [
            "dircomply = dircomply.main:main",  # entry point
        ],
    },    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",        
    ],
    python_requires=">=3.7",           # Specify minimum Python version
)
