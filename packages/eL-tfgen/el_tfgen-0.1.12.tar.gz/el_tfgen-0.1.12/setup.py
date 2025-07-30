from setuptools import setup, find_packages

setup(
    name="eL-tfgen",
    version="0.1.12",
    description="Generate Terraform modules from documentation using AI",
    author="eLTitans",
    packages=find_packages(),
    install_requires=[
        "playwright",
        "beautifulsoup4",
        "openai",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "tfgen=tfgen.cli:cli",
        ],
    },
    python_requires=">=3.8",
) 