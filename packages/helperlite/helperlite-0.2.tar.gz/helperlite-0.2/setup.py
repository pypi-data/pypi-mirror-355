from setuptools import setup, find_packages

setup(
    name="helperlite",
    version="0.2",
    packages=find_packages(),
    install_requires=[],
    description="A small helper tool for CLI automation.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="hi",
    author_email="your@email.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
