from setuptools import setup, find_packages
from tkla_utils_flask_api.version import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tkla_utils_flask_api',
    version=__version__,
    description='JWT, hashing y utilidades para APIs Flask',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Lovenson Pierre',
    packages=find_packages(),
    install_requires=[
        'Flask',
        'PyJWT',
        'bcrypt'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.7',
)
