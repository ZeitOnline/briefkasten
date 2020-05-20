from setuptools import setup

version = '0.3.0.dev'
name = 'briefkasten_watchdog'

setup(
    name=name,
    version=version,
    description='Perform functional testing of a Briefkasten instance',
    long_description="""
        Part of the `ZeitOnline Briefkasten <https://github.com/ZeitOnline/briefkasten>`_ project,
        this allows administrators to perform a fully functional test of their running instances.
        See the `documentation <https://github.com/ZeitOnline/briefkasten#monitoring>`_ for details.""",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: BSD License',
    ],
    packages=[name],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'click',
        'imapclient',
        'zope.testbrowser',
        'pyquery',
        'pyramid_mailer',
    ],
    extras_require={
        'development': [
            'devpi-client',
        ],
    },
    entry_points="""
        [console_scripts]
        watchdog = briefkasten_watchdog:main
    """,
)
