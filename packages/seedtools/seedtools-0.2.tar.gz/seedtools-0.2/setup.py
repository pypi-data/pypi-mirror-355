from setuptools import setup,find_packages





setup(
    name="seedtools",
    version="0.2",
    author="Rashesh",
    author_email="rashesh369@gmail.com",
    packages=find_packages(),
     description='A lightweight toolkit for loading and managing versioned seed datasets in Python.',
    long_description=open("readme.md",encoding="utf-8").read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
        install_requires=[
        "python-dotenv"
    ],
    
)