from setuptools import setup

setup(
    name='ttktooltip',
    version='1.1',
    description='A simple tooltip widget for Tkinter',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    py_modules=['ttktooltip'],  # Correct for single-file module
    install_requires=[],  # No need to list 'tkinter' – it's built into Python
    author='Prashant Mandal',
    author_email='prashant7mandal@gmail.com',
    url='https://github.com/prashant-mandal/ttktooltip',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)

# Make sure to update the version number
# Install the package using:
# pip install setuptools wheel twine

### To publish this package, run:
# python setup.py sdist bdist_wheel
# twine upload dist/*
# Eneter the API token when prompted.

