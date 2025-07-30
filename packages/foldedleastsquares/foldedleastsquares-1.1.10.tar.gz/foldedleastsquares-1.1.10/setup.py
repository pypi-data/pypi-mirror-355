import setuptools
from setuptools import setup
from os import path


exec(open(path.join("foldedleastsquares", 'version.py')).read())

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

    
setup(name='foldedleastsquares',
    version=TLS_VERSIONING,
    description='An optimized transit-fitting algorithm to search for periodic features in light curves',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/martindevora/tls',
    author='Martín Dévora Pajares',
    author_email='martin.devora.pajares@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'': ['*.csv', '*.cfg']},
    install_requires=[
        'astropy==7.0.1',
        'astroquery==0.4.10',
        'numpy==2.2.5',
        'numba==0.61.2',
        'scipy==1.15.2',
        'tqdm',
        'batman-package==2.5.3',
        'argparse',
        'configparser',
        'torch==2.7.0'
        ],
    extras_require = {
        'cupy': '13.4.1'
    }
)
