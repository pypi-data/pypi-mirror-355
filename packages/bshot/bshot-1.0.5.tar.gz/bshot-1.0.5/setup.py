import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bshot",
    version="1.0.4",
    author="Pradish Bijukchhe",
    author_email="pradishbijukchhe@gmail.com",
    description=(
        "Python package to take screenshots of windows that are in background"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sandbox-pokhara/bshot",
    project_urls={
        "Bug Tracker": "https://github.com/sandbox-pokhara/bshot/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    include_package_data=True,
    package_dir={"bshot": "bshot"},
    python_requires=">=3",
    install_requires=["numpy", "pywin32"],
)
