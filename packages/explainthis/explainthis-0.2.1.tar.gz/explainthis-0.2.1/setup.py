from setuptools import setup, find_packages

setup(
    name="explainthis",
    version="0.2.1",
    description="Beginner-friendly error tracing for Python.",
    author="Jaden Gregory",
    author_email="jaden.andru@gmail.com",
    url="https://github.com/00-Masterpiece/ExplainThis",
    license="Proprietary",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "rich>=13.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: Other/Proprietary License"
    ],
    python_requires='>=3.7',
)
