from setuptools import setup, find_packages


setup(
    name="frst-auth-cli",
    version="1.0.1",
    description="CLI to manage and verify user and app permissions on the FRST platform.",  # noqa E501
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Marcos William Ferretti",
    author_email="ferretti.spo@gmail.com",
    url="https://github.com/FRST-Falconi/frst-auth-cli",
    packages=find_packages(where=".", exclude=("tests",)),
    package_dir={"": "."},
    install_requires=[
        "typer>=0.12.0",
        "requests>=2.25.0"
    ],
    entry_points={
        "console_scripts": [
            "frst-auth-cli=frst_auth_cli.cli:app"
        ]
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Security",
        "Topic :: Utilities"
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
