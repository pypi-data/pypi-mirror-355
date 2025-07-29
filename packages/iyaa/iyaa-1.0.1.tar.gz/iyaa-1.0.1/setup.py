from setuptools import setup, find_packages

setup(
    name="iyaa",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "questionary"
    ],
    entry_points={
        "console_scripts": [
            "iyaa=iya.cli:main"
        ]
    },
    author="Piyush Pal",
    author_email = "piyushpal9532@gmail.com",
    description="Professional Project Bootstrap CLI",
    keywords="cli project-generator boilerplate",
    license="MIT",
    python_requires=">=3.7"
)
