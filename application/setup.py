from setuptools import setup, find_packages

version = '0.1.10dev0'


setup(name='briefkasten',
    version=version,
    description='a reasonably secure web application for submitting content anonymously',
    long_description="",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: BSD License',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Pyramid',
        'pyramid_deform',
        'deform',
        'Paste',
        'zope.testbrowser',
        'pyquery',
    ],
    extras_require={
        "tests": [
            'wsgi_intercept',
            'zope.testbrowser'],
    },
    test_suite="briefkasten",
    entry_points="""
        [paste.app_factory]
        main = briefkasten:main
    """,
    message_extractors={'briefkasten': [
        ('**.py', 'lingua_python', None),
        ('**.zcml', 'lingua_xml', None),
        ('**.pt', 'lingua_xml', None),
    ]},
)
