#!/usr/bin/env python

import os
import re

from setuptools import find_packages, setup


def get_long_description():
    for filename in ("README.rst",):
        with open(filename, "r") as f:
            yield f.read()


def get_version(package):
    with open(os.path.join(package, "__init__.py")) as f:
        pattern = r'^__version__ = [\'"]([^\'"]*)[\'"]'
        return re.search(pattern, f.read(), re.MULTILINE).group(1)


setup(
    name="django-graphene-social-auth",
    version=get_version("graphql_social_auth"),
    license="MIT",
    description="Python Social Auth support for Django GraphQL",
    long_description="\n\n".join(get_long_description()),
    author="Michael",
    author_email="ademictech@gmail.com",
    maintainer="Michael",
    maintainer_email="ademictech@gmail.com",
    url="https://github.com/Ademic2022/django-graphene-social-auth/",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "Django>=3.2",
        "graphene-django>=3.0.0",
        "social-auth-app-django>=5.0.0",
        "django-filter>=24.3",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
    ],
    zip_safe=False,
    package_data={
        "graphql_social_auth": [
            "locale/*/LC_MESSAGES/django.po",
            "locale/*/LC_MESSAGES/django.mo",
        ],
    },
    extras_require={
        "jwt": ["django-graphql-jwt>=0.4.0"],
        "test": [
            "Django>=3.2",
            "graphene-django>=3.0.0",
            "social-auth-app-django>=5.0.0",
            "coverage>=7.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-django>=4.5.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
)
