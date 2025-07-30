from setuptools import setup, find_packages

setup(
    name="sabbylives",
    version="666.0.0",
    author="Commonwealthrocks",
    description="Death and hatred to mankind.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'sabbylives = sabbylives.__main__:main'
        ],
    },
)
