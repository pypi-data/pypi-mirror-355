import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="skpmem",
    version="0.2.0",
    install_requires=["aiosqlite", "setuptools"],
    packages=setuptools.find_packages(),
    description="Persistent Memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="sugarkwork",
    url="https://github.com/sugarkwork/pmem",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires='>=3.10',
)
