from setuptools import setup, find_packages
import os
import sys

# Dynamically calculate the version based on moderation.VERSION.
version = __import__("moderation").__version__

tests_require = [
    "unittest2py3k",
    "django>=1.11",
    "django-webtest",
    "webtest",
    "mock",
    "pillow",
]

install_requires = ["django>=1.11", "django-model-utils"]

# override django-model-utils version in requirements file if DJANGO env is set
setup(
    name="django-moderation",
    version=version,
    description="Generic Django objects moderation application",
    long_description=open("README.rst").read()
    + "\n"
    + open(os.path.join("docs", "history.rst")).read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
    ],
    keywords="django moderation models",
    author="Dominik Szopa",
    author_email="dszopa@gmail.com",
    url="http://github.com/dominno/django-moderation",
    license="BSD",
    packages=find_packages(".", exclude=("tests", "example_project")),
    include_package_data=True,
    tests_require=tests_require,
    test_suite="runtests.runtests",
    install_requires=install_requires,
    zip_safe=False,
)
