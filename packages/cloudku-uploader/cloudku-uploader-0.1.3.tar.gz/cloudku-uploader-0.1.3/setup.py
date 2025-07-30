from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='cloudku-uploader',
    version='0.1.3',
    description='Python client for uploading files to cloudkuimages.guru',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Nauval sada',
    author_email='akunv5783@gmail.com',
    url='https://pypi.org/project/cloudku-uploader/',
    packages=find_packages(),
    install_requires=['requests'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)
