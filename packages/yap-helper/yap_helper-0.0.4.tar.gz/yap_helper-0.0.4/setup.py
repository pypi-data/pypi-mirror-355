from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 11',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]

setup(
    name='yap_helper',
    version='0.0.4',
    description='a helper library for those that yap',
    long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='',
    author='Graham "yap.athy" Lasseigne',
    author_email='grahamlasseigne@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords='yap',
    packages=find_packages(),
    install_requires=[''], # if any of my helper scripts need a separate library
    include_package_data=True
) 

# python setup.py sdist
# pypi-AgEIcHlwaS5vcmcCJGQ5MzE4NjZjLTlmYWQtNDk0NS1iYTI4LWQ0NTMyODEyNjFkOAACElsxLFsieWFwLWhlbHBlciJdXQACLFsyLFsiZjdlZTc3NmQtMmFmZC00YjM3LWIzYTItNGU2NTdmYzkyZmNlIl1dAAAGILcGjINrVVAjZvLGABu4Jvn4iin4HP960d7PB0fd6hcy