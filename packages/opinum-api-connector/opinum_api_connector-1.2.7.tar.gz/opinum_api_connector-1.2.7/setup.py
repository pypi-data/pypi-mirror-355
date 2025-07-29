import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="opinum-api-connector",
    version="1.2.7",
    author="Opinum",
    author_email="support@opinum.com",
    description="Package to interact with the Opinum API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opinum/opinum-api-connector",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'requests',
        'requests_oauthlib',
        'oauthlib'
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
