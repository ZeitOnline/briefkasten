from setuptools import setup

version = '0.1.10-dev'


setup(name='briefkasten_watchdog',
    version=version,
    description='test if a given briefkasten instance is working properly',
    long_description="",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: BSD License',
    ],
    packages=['briefkasten_watchdog'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'imapclient',
        'zope.testbrowser',
        'pyquery',
        'pyramid_mailer',
    ],
    extras_require={
        "tests": [
            'wsgi_intercept',
            'zope.testbrowser'],
    },
    test_suite="briefkasten",
    entry_points="""
        [console_scripts]
        watchdog = briefkasten_watchdog:main
    """,
)
