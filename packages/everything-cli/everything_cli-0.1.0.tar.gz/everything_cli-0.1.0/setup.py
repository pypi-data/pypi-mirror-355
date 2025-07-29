from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="everything-cli",
    version="0.1.0",
    author="Martin V.",
    author_email="marci.vas@hotmail.com",
    description="A custom command-line interface similar to diskpart",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'cmd2>=2.5.0'
    ],
    entry_points={
        'console_scripts': [
            'everything=everything:main',
        ],
    },
)
