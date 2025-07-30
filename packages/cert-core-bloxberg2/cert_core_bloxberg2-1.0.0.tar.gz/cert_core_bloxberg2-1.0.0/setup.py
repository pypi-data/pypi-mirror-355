import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open('requirements.txt') as f:
    install_reqs = f.readlines()
    reqs = [str(ir) for ir in install_reqs]

with open(os.path.join(here, 'README.md')) as fp:
    long_description = fp.read()

setup(
    name='cert-core-bloxberg2',
    version='1.0.0',
    description='Blockcerts core models for python',
    author='info@blockcerts.org',
    tests_require=['tox'],
    url='https://gitlab.mpcdf.mpg.de/cert-issuer/cert-core.git',
    license='MIT',
    author_email='info@blockcerts.org',
    long_description=long_description,
    long_description_content_type='text/markdown', 
    packages=find_packages(),
    install_requires=reqs
)
