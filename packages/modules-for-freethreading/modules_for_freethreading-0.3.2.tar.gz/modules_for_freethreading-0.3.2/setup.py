from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="modules_for_freethreading",
    version="0.3.2",
    author="Locked-chess-official",
    author_email="13140752715@163.com",
    description="A module to handle module compatibility between free-threading and regular Python builds",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Locked-chess-official/modules_for_freethreading",
    py_modules=["modules_for_freethreading"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
    install_requires=[
        "packaging>=21.0",
    ],
    project_urls={
        "Bug Reports": "https://github.com/Locked-chess-official/modules_for_freethreading/issues",
        "Source": "https://github.com/Locked-chess-official/modules_for_freethreading",
    },
)
