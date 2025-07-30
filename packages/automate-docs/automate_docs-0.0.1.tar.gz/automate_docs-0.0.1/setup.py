from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="automate-readme",
    version="0.0.1",
    author="Natalio Gomes",
    author_email="natalio.gomes@libertymutual.com",
    description="A tool to automate readme generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/automate-docs",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "python-dotenv",
        "python-decouple",
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # or your license
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
    ],
    license="MIT",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            # If your package has CLI, e.g.,
            # "automate-docs=automate_docs.cli:main",
        ],
    },
)
