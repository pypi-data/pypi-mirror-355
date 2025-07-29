from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kat_cipher",
    version="1.0.1",  # Updated version to resolve PyPI upload conflict
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.9.0.80",
        "numpy>=1.26.0",
        "PyQt6>=6.4.2",
        "PyQt6-tools==6.4.2.3.3",
        "PyQt6-plugins==6.4.2.2.3"
    ],
    entry_points={
        "console_scripts": [
            "kat_cipher=kat_cipher.gui:main",  # Ensure correct import path
        ],
    },
    author="Yashkumar Dubey",
    author_email="your.email@example.com",  # Add a valid email
    description="A Python package for Sanskrit-based text steganography in images.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YashAPro1/kat_cipher.git",  # Add your GitHub repo link
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
