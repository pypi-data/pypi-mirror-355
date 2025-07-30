# -*- coding: utf-8 -*-
__author__ = 'chenli'

import setuptools

setuptools.setup(
    name='tqsdk-zq',
    version="1.0.3",
    description='TianQin SDK - zq lib',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    url='https://www.shinnytech.com/tqsdk',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3',
    install_requires=[
        'tqsdk-zq-server',
        'tqsdk-zq-pgserver',
        'tqsdk-zq-proxy',
        'tqsdk-zq-history',
        'filelock',
        'psutil',
    ],
    entry_points={
        'console_scripts': [
            'tqsdk-zq = tqsdk_zq.cli:main',
        ],
    }
)
