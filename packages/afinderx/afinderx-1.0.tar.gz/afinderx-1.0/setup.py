from setuptools import setup, find_packages

setup(
    name="afinderx",
    version="1.0",
    author="Babar Ali Jamali",
    author_email="babar995@gmail.com",
    description="Android opened devices finder and port scanner",
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "afinderx=afinderx.afinderx:main"
        ],
    },
)
