from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name="tc-temporal-backend",
    version="1.1.3",
    author="Mohammad Amin Dadgar, TogetherCrew",
    maintainer="Mohammad Amin Dadgar",
    maintainer_email="dadgaramin96@gmail.com",
    packages=find_packages(),
    description="This repository is TogetherCrew's temporal io python shared codes",
    long_description=open("README.md").read(),
    install_requires=requirements,
)
