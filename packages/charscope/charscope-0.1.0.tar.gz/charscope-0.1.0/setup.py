from setuptools import setup, find_packages

setup(
    name="charscope",
    version="0.1.0",
    description="Character analysis and visualization for ASCII and UTF-8",
    author="Eden Simamora",
    author_email="aeden6877@gmail.com",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "colorama",
        "pyfiglet"
    ],
    python_requires=">=3.7",
    include_package_data=True,
    long_description = open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    url="https://github.com/yourname/CharScope"
)
