# setup.py

from setuptools import setup, find_packages

setup(
    name='mongofw',
    version="1.0.1",
    packages=find_packages(),
    install_requires=['pymongo'],
    author='Muslu Yüksektepe (musluyuksektepe@gmail.com)',
    author_email='musluyuksektepe@gmail.com',
    description='Python + Mongo',
    long_description=open('README.md', encoding="utf-8").read(),
    long_description_content_type='text/markdown',
    url='https://github.com/muslu/mongofw',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
