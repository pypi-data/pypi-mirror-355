from setuptools import setup

setup(
    name='bistosi',
    version='0.1.7',
    author='Amirreza Taherkhani',
    author_email='ar.taher404@gmail.com',
    packages=['bistosi'],
    install_requires=[
        'python-dotenv',
        'celery',
    ],

    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10',
    ],
)
