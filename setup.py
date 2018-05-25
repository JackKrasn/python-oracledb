from setuptools import setup, find_packages
from os.path import join, dirname
import oracledb

setup(
    name='oracledb',
    classifiers=['Programming Language :: Python :: 2.7', ],
    version=oracledb.__version__,
    author=oracledb.__author__,
    author_email=oracledb.__author_email__,
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    include_package_data=True,
    install_requires=['jinja2', 'cx_Oracle']
)


