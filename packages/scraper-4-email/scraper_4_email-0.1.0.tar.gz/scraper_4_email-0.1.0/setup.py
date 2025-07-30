from setuptools import setup, find_packages

setup(
    name="scraper-4-email",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "pandas",
        "openpyxl",
    ],
    entry_points={
        "console_scripts": [
            "scraper-4-email=scraper_4_email.cli:main",
        ],
    },
    author="Franck da COSTA",
    description="Scrape e-mails from Excel files on websites.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)