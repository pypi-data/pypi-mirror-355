from setuptools import setup, find_packages

setup(
    name='cloudku-uploader',
    version='0.1.1',
    description='Python client for uploading files to cloudkuimages.guru',
    author='Nauvalsada',
    author_email='akunv5387@gmail.com',
    packages=find_packages(),
    install_requires=['requests'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)