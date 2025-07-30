from setuptools import setup

setup(
    name='edcode',
    version='1.0',
    py_modules=['edcode'],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'edcode=edcode:main',
        ],
    },
    #url='https://github.com/'
)
