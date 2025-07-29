import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(

    name="marlin_brahma", # Replace with your own username
    version="3.7.0",
    author="Rahul Tandon",
    author_email="rahul@vixenintelligence.com",
    description="MARLIN Learn | GA Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/vixencapital/brahma/archive/0.0.5.tar.gz",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
