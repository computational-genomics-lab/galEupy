from setuptools import setup, find_packages

# Read version from galEupy/version.py
exec(open('galEupy/version.py').read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='galEupy',
    version=__version__,
    author='Arijit Panda, CGLAB; Aditya Upadhyay, CGLAB',
    author_email='arijpanda@csiriicb.res.in; aditya.upadhyay@csiriicb.res.in',
    packages=find_packages(),  # Automatically find all packages and subpackages
    package_dir={'galEupy': 'galEupy'},
    package_data={'galEupy': ['BioFile/*', 'data/DbSchema/*', 'data/DefaultConfig/*', 'data/CommonData/*']},
    description="Python module for gal",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/computational-genomics-lab/GAL',
    install_requires=[
        'pathlib>=1.0',
        'pymysql>=1.0.0',
        'numpy>=1.16',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    entry_points={
        'console_scripts': [
            'galEupy = galEupy.__main__:main'
        ]
    }
)
