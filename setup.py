"""
Setup configuration for django-flex-importer
"""
from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-flex-importer',
    version='1.1.0',
    author='twine003',
    author_email='',  # Agrega tu email si quieres
    description='Sistema flexible de importación de datos para Django con soporte para XLSX, CSV y JSON',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/twine003/django-flex-importer',
    project_urls={
        'Bug Reports': 'https://github.com/twine003/django-flex-importer/issues',
        'Source': 'https://github.com/twine003/django-flex-importer',
        'Documentation': 'https://github.com/twine003/django-flex-importer#readme',
    },
    packages=find_packages(exclude=['example_app', 'config', 'tests']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
    ],
    python_requires='>=3.7',
    install_requires=[
        'Django>=3.2',
        'openpyxl>=3.0.0',
    ],
    extras_require={
        'async': ['celery>=5.0.0', 'redis>=4.0.0'],
        'dev': [
            'pytest>=7.0.0',
            'pytest-django>=4.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'isort>=5.0.0',
        ],
    },
    keywords='django import excel csv json xlsx importer data-import bulk-import',
    zip_safe=False,
)
