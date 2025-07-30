from setuptools import setup, find_packages

setup(
    name="envtwin",
    version="1.1.0",
    description="Instant Environment Recreator: snapshot and share your dev environment.",
    author="Syntax-XXX",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "envtwin=envtwin.__main__:main"
        ]
    },
    python_requires=">=3.6",
    include_package_data=True,
    license="MIT",
)
