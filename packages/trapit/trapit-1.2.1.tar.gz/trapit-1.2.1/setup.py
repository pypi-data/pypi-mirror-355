import setuptools

with open("trapit/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trapit",
    version="1.2.1",
    author="Brendan Furey",
    author_email="brenpatf@gmail.com",
    description="Trapit python utility for Math Function Unit Test design pattern",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/brenpatf/trapit_python_tester",
    packages=["trapit"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
)