import setuptools

# get long_description
with open("README.md", "r") as fh:
    long_description = fh.read()

# get required lib
with open("script/requirements.txt", "r") as file:
    requirements = file.read().strip().split("\n")

setuptools.setup(
    name="infra_analytics",
    version="0.0.4",
    author="hautx2",
    author_email="hautx2@fpt.com",
    description="Sort description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    # requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
