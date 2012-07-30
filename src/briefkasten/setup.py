from setuptools import setup, find_packages

version = '0.1'


setup(name='briefkasten',
    version=version,
    description='A secure drop box',
    long_description="",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Pyramid',
        'pyramid_deform',
        'deform',
    ],
    extras_require={
        "sphinx": ["Sphinx", "repoze.sphinx.autointerface"],
        "tests": ['wsgi_intercept', 'zope.testbrowser']
    },
    test_suite="briefkasten",
    entry_points="""
        [paste.app_factory]
        main = briefkasten:main
        [paste.filter_factory]
        proxy = briefkasten.proxy:ProxyFactory
    """,
    message_extractors={'briefkasten': [
        ('**.py', 'lingua_python', None),
        ('**.zcml', 'lingua_xml', None),
        ('**.pt', 'lingua_xml', None),
    ]},
)
