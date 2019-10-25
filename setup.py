from setuptools import setup, find_packages
import os
import sys

version = '0.6.0'

tests_require = [
    'django>=1.11,<=2.2',
    'django-webtest',
    'webtest',
    'mock',
    'pillow',
]

# ipython>2 is only supported on Python 2.7+
if sys.hexversion < 0x02070000:
    tests_require = ['ipython>=0.10,<2'] + tests_require

if sys.hexversion >= 0x03000000:
    tests_require = ['unittest2py3k'] + tests_require
else:
    tests_require = ['unittest2'] + tests_require

setup(
    name='django-moderation',
    version=version,
    description='Generic Django objects moderation application',
    long_description=open('README.rst').read() + '\n' +
                     open(os.path.join('docs', 'history.rst')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
    ],
    keywords='django moderation models',
    author='Dominik Szopa',
    author_email='dszopa@gmail.com',
    url='http://github.com/dominno/django-moderation',
    license='BSD',
    packages=find_packages('.', exclude=('tests', 'example_project')),
    include_package_data=True,
    tests_require=tests_require,
    test_suite='runtests.runtests',
    install_requires=[
        'django>=1.11,<=2.2',
        'django-model-utils',
    ],
    zip_safe=False,
)
