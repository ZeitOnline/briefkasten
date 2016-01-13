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
        'Pyramid<1.7',
        'pyramid_chameleon',
        'colander',
        'diazo',
        'itsdangerous',
        'python-gnupg',
        'repoze.xmliter',
        'Paste',
    ],
    extras_require={
        'development': [
            'webtest',
            'flake8',
            'mock',
            'pep8 < 1.6',
            'pyramid_debugtoolbar',
            'pytest <2.8',
            'py >= 1.4.17',
            'pyflakes < 0.9',
            'pytest-flakes',
            'pytest-pep8',
            'pytest-cov',
            'pytest-capturelog',
            'tox',
            'pyquery',
            'mr.hermes',
            'setuptools-git',
            'devpi-client',
            'click',
        ],
    },
    entry_points="""
        [paste.app_factory]
        main = briefkasten:main
        [pytest11]
        briefkasten = briefkasten.testing
    """,
    message_extractors={'briefkasten': [
        ('**.py', 'lingua_python', None),
        ('**.zcml', 'lingua_xml', None),
        ('**.pt', 'lingua_xml', None),
    ]},
)
