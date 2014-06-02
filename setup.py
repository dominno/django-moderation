from setuptools import setup, find_packages
import os
import sys

version = '0.3.5'

tests_require = ['django>=1.3.7,<1.7', 'django-webtest>=1.5.7,<1.6',
                 'webtest>=2.0,<2.1', 'mock', 'pillow', 'unittest2', 'ipdb']

# ipython>2 is only supported on Python 2.7+
if sys.hexversion < 0x02070000:
    tests_require = ['ipython>=0.10,<2'] + tests_require

setup(name='django-moderation',
      version=version,
      description="Generic Django objects moderation application",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        ],
      keywords='django moderation models',
      author='Dominik Szopa',
      author_email='dszopa@gmail.com',
      url='http://github.com/dominno/django-moderation',
      license='BSD',
      packages = find_packages('.'),

      include_package_data=True,
      tests_require=tests_require,
      test_suite='runtests.runtests',
      install_requires=[
          'django>=1.3.7,<1.7',
          'setuptools',
      ],
      zip_safe=False,
      )
