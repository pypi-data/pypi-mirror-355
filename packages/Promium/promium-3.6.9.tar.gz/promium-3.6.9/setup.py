
import codecs
from setuptools import setup, find_packages


REQUIREMENTS = [
    'six>=1.10.0',
    'json_checker>=1.2.1',
    'urllib3>=2.0.2',
    'py>=1.5.2',
    'pytest>=5.0.0',
    'pytest_rerunfailures>=4.1.0',
    'pytest-forked>=0.2',
    'pytest-instafail>=0.3.0',
    'deepdiff>=5.7.0',
    'selenium>=4.10.0',
]


setup(
    name='Promium',
    version='3.6.9',
    install_requires=REQUIREMENTS,
    author='Denis Korytkin, Nataliia Guieva, '
           'Roman Zaporozhets, Vladimir Kritov, '
           'Oleh Dykusha',
    project_urls={
        'Home page': 'https://none',
        'Documentation': 'https://none',
    },
    description='Selenium wrapper for testing Web UI',
    long_description=codecs.open('README.rst', 'r', 'utf-8').read(),
    keywords=['Testing UI', 'Selenium', 'PageObject', 'Selenium wrapper'],
    platforms=['linux'],
    packages=find_packages(),
    entry_points={'pytest11': ['promium = promium.plugin']},
    python_requires='>=3.10, <4',
    classifiers=[
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Testing',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
    ]
)
