from setuptools import setup

setup(
    name='dct',
    version='0.1.5',
    description='Distributed Cognitive Toolkit',
    url='https://github.com/wandgibaut/dct',
    author='Wandemberg Gibaut',
    author_email='wgibaut@mail.com',
    license='MIT',
    packages=['dct'],
    install_requires=[
        'flask>=2.2.2',
        'pymongo>=4.2.0',
        'redis>=4.3.4',
        'requests>=2.28.1',
        'networkx==2.8.6',
        'matplotlib==3.5.3'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

