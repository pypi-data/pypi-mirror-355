from setuptools import setup, find_packages

setup(
    name='totoapicontroller',
    version='1.1.3',
    description='API Controller for Toto APIs',
    author='nicolasances',
    author_email='nicolas.matteazzi@gmail.com',
    packages=find_packages(),
    install_requires=[
        "PyJWT",
        "Flask-Cors",
        "Flask", 
        "google-cloud-secret-manager", 
        "boto3"
    ]
)
