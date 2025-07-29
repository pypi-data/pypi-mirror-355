from setuptools import setup, find_packages

setup(
    name="securitykey",
    version="0.1.0",
    author="JTCoder8290",
    author_email="jacktay.yujie@gmail.com",
    description="A Python module to generate and verify security keys for unique identification",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    py_modules=["securitykey"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
