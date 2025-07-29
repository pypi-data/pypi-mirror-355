from setuptools import setup, find_packages

setup(
    name='codecompanion',
    version='0.1.0',
    description='Smart code analysis companion for Python developers',
    author='Eden Simamora',
    author_email='aeden6877@gmail.com',
    packages=find_packages(),
    install_requires=[
        'autopep8',
        'pyflakes',
        'radon',
        'rich',
        'typeguard',
        'black',
        'docstring-parser',
        'jedi',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
