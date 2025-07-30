from setuptools import setup, Extension

module = Extension(
    name="sysmess",
    sources=["src/sysmessmodule.c"],
)

import os

with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="sysmess",
    version="0.1.5",
    author="Luke Canada",
    author_email="canadaluke888@gmail.com",
    description="Fancy terminal message box renderer using Unicode box characters and ANSI styling",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    ext_modules=[module],
)