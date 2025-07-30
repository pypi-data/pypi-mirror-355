from setuptools import setup, find_packages

setup(
    name="doc2dict",
    version="0.3.5",
    packages=find_packages(),
    install_requires=[
        'Cython==3.0.11',  # Pin the exact version selectolax needs
        'selectolax',
        'xmltodict',
        'pypdfium2'
    ],
    python_requires=">=3.8"
)