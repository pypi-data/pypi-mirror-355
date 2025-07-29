from setuptools import setup, find_packages

setup(
   name='connect-mydb', 
    version='0.1.1', 
    packages=find_packages(), 
    author='Mohamed Khasim', 
    description='A lightweight Python package that helps you connect to a MySQL database with a single line of code', 
    long_description=open('README.md').read(), 
    long_description_content_type='text/markdown',
    url='https://github.com/k3XD16/connect-mydb',
    classifiers=[ 
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=[
        'mysql-connector-python'
    ]
)