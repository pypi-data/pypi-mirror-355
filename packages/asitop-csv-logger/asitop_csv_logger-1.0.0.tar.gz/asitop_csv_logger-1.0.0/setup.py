from setuptools import setup, find_packages

setup(
    name="asitop-csv-logger",
    version="1.0.0",
    author="Biswareet Panda",
    author_email="biswa.gunu2003@gmail.com",
    description="CSV logger for Apple Silicon using asitop",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Intruder2614/asitop_raw_data_csv",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "psutil",  # add more dependencies if you use them
    ],
    entry_points={
        "console_scripts": [
            "asitop-csv-logger = asitop_csv_logger.asitop_csv_logger:main"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS",
        "License :: OSI Approved :: MIT License"
    ],
    license="MIT"
)
