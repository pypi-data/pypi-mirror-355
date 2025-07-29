from setuptools import setup, find_packages

setup(
    name="apitester-lite",
    version="0.3.0",
    packages=find_packages(),
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "apitester-lite = apitester_lite.cli:main"
        ]
    },
    author="Shrinidhi",
    description="Lightweight API testing CLI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Shrinidhi064/apitester-lite",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
