from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="allyin",  # Top-level package name
    version="0.1.2",
    description="Allyin: Modular AI tools for enterprise data processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Niraj Dalavi",
    author_email="niraj@allyin.ai",
    url="https://github.com/AllyInAi/libs",  # Update to your actual repo
    packages=find_packages(include=["allyin", "allyin.*"]),
    install_requires=[
        # "openai-whisper==20240930",
        # "openai-whisper @ git+https://github.com/openai/whisper.git",
        "readability-lxml==0.8.4.1",
        "beautifulsoup4==4.13.4",
        "pillow==11.2.1",
        "pytesseract==0.3.13",
        "pymupdf==1.26.0",
        "python-pptx==1.0.2",
        "pytest==8.4.0",
        "python-docx==1.1.2",
        "pandas==2.3.0",
        "openpyxl==3.1.5",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",  # Or your license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)