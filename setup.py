from setuptools import setup, find_packages
import os

version = '0.3.2'

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
      packages = find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      install_requires=[
          'setuptools',
      ],
      zip_safe=False,
      )
