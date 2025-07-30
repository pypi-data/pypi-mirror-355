from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    description = f.read()

setup(
    name='sm_env_read',
    version='1.0.4',
    description='read env secrets from aws secrets manager',
    author='Deepak M S',
    author_email='deepakcoder80@gmail.com',
    packages=find_packages(),
    install_requires=[
        'boto3'
    ],
    long_description=description,
    long_description_content_type="text/markdown"
)