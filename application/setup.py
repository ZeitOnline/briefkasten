from setuptools import setup, find_packages


setup(
    name='briefkasten',
    version_format="{tag}.{commitcount}+{gitsha}",
    description='a reasonably secure web application for submitting content anonymously',
    long_description="",
    maintainer=u'Tom Lazar',
    maintainer_email=u'tom@tomster.org',
    url=u'https://github.com/ZeitOnline/briefkasten',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: BSD License',
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'briefkasten': [
            'templates/*.*',
            'tests/*.*',
            'tests/gpghome/*.*',
        ],
    },
    zip_safe=False,
    setup_requires=[
        'setuptools-git >= 0',
        'setuptools-git-version'
    ],
    install_requires=[
        'Pyramid<2.1',
        'pyramid_chameleon',
        'click',
        'colander',
        'diazo',
        'humanfriendly',
        'itsdangerous',
        'jinja2',
        'python-gnupg',
        'repoze.xmliter',
        'Paste',
        'watchdog',
        'PyYAML',
    ],
    extras_require={
        'development': [
            'tox<4.0',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = briefkasten:main
        [pytest11]
        briefkasten = briefkasten.testing
        [console_scripts]
        debug = briefkasten.commands:debug
        worker = briefkasten.commands:worker
        janitor = briefkasten.commands:janitor
    """,
    message_extractors={'briefkasten': [
        ('**.py', 'lingua_python', None),
        ('**.zcml', 'lingua_xml', None),
        ('**.pt', 'lingua_xml', None),
    ]},
)
