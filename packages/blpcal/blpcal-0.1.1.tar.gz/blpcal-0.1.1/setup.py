from setuptools import setup, find_packages

setup(
    name="blpcal",
    version="0.1.1",
    author="mohitkumar",
    author_email="ronnycrush198@gmail.com",
    description="A simple calculator",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
    license='MIT',  # explicitly specify license
    entry_points={
        "console_scripts": [
            "blpcal=blpcal.calculator:main",
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
