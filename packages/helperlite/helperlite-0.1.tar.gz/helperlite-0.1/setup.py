from setuptools import setup, find_packages

setup(
    name="helperlite",
    version="0.1",
    packages=find_packages(),
    install_requires=["pynput"],
    author="Trần",
    author_email="admin@example.com",
    description="Helper tool for advanced devs",
    long_description="Advanced support utility for developers working in secure environments.",
    long_description_content_type="text/plain",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)
