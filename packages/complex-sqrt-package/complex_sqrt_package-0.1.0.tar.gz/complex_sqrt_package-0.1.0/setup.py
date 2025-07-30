from setuptools import setup, find_packages

setup(
    name='complex_sqrt_package',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A package to calculate complex square roots interactively.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
