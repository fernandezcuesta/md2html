#!/usr/bin/env python
from setuptools import setup

requires = ['csscompressor >= 0.9.3', 'Jinja2 >= 2.7.3', 'rfc3987', 'python-dateutil', 'six',
            'Markdown >= 2.6.1', 'MarkupSafe', 'Pygments >= 2.0.2']

entry_points = {
    'console_scripts': [
         'md2html = mdtohtml:argument_parse'
            ]
}


README = open('README.md').read()
CHANGELOG = open('changelog.md').read()


setup(
    name="md2html",
    version="0.0.3",
    url='https://github.com/fernandezcuesta/md2html',
    author='JM Fernandez',
    author_email='fernandez.cuesta@gmail.com',
    description="Yet another markdown to HTML convertor, with embedded images and CSS",
    long_description=README + '\n' + CHANGELOG,
    packages=['mdtohtml'],
    include_package_data=True,
    install_requires=requires,
    entry_points = entry_points,
#    {
#       'console_scripts': [
#            'convierte = md2html:argument_parse'
#       ]
#    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
         'Environment :: Console',
         'License :: OSI Approved :: GNU Affero General Public License v3',
         'Operating System :: OS Independent',
         'Programming Language :: Python :: 2',
         'Programming Language :: Python :: 2.7',
         'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    test_suite='tests',
)
