# setup.py
from setuptools import setup, find_packages

setup(
    name='demo_package_2025',
    version='0.1',
    packages=find_packages(),
    description='A simple demo package for adding two numbers',
    long_description=open('README.md', encoding='utf8').read(),
    long_description_content_type='text/markdown',
    author='Jaehoon Lee',
    author_email='68533989+jaehoon0905@users.noreply.github.com',
    url='https://github.com/jaehoon0905/demo_package_2025',
    license='MIT',
    keywords='demo package add numbers',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
    install_requires=[],
)