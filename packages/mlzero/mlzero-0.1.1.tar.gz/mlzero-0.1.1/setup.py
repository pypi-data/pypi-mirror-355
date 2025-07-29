from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
print(long_description)
setup(
    name='mlzero',
    version='0.1.1',
    description='Machine Learning from Scratch - Educational Python Library',
    author='Aditya Veerkar',
    author_email='bzubs011@gmail.com',
    url='https://github.com/bzubs/MLzero',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
