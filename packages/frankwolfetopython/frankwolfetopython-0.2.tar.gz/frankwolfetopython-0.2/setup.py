from setuptools import setup, find_packages

requirements = ["juliacall>=0.9.0",
                "numpy>=1.20.0"]

with open("README.md", "r") as f:
    desc = f.read()

setup(
    name="frankwolfetopython",
    version="0.2",
    packages=find_packages(),
    install_requires=requirements,
    author="Matthew Mione",
    author_email="matthewmione@gmail.com",
    description="A Python wrapper for the FrankWolfe.jl Julia package, \
        providing an interface for Frank-Wolfe optimization methods.",
    long_description=desc,
    long_description_content_type="text/markdown",
)

