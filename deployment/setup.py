from setuptools import setup

version = "0.1alpha1"

setup(
    version=version,
    name="briefkasten_fabfiles",
    author='Tom Lazar',
    author_email='tom@tomster.org',
    url='http://github.com/tomster/bsdploy',
    include_package_data=True,
    zip_safe=False,
    packages=['fabric_scripts'],
    install_requires=[
        'setuptools',
        'Fabric<1.8.3',
    ],
)
