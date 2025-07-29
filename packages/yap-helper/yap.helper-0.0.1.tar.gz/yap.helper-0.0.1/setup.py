from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 11',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]

setup(
    name='yap.helper',
    version='0.0.1',
    description='A helper python library to assist a system engineer',
    long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='',
    author='Graham "yap.athy" Lasseigne',
    author_email='grahamlasseigne@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords='yap',
    packages=find_packages(),
    install_requires=['']
)