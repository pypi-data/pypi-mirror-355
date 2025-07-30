from setuptools import setup, find_packages

setup(
    name='aroma-py',
    version='0.0.1',
    description='A lightweight Python web framework like Aroma.js',
    author='Aavesh Jilani',
    author_email='aavesh@dragon-lang.org',
    url='https://github.com/aaveshdev/aroma-py',
    packages=find_packages(),
    install_requires=[
        'Jinja2>=3.0.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)