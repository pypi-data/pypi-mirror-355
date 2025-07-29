from setuptools import setup, find_packages

setup(
    name='mlzero',
    version='0.1.0',
    description='Machine Learning from Scratch - Educational Python Library',
    author='Aditya Veerkar',
    author_email='bzubs011@gmail.com',
    url='https://github.com/bzubs/MLzero',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    python_requires='>=3.7',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
