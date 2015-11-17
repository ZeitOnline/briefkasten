from setuptools import setup, find_packages

version = '0.2.0.dev0'


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
        'Pyramid<1.6',
        'pyramid_deform',
        'pyramid_chameleon',
        'deform',
        'diazo',
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
        ],
    },
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
