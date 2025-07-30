from setuptools import setup, find_packages

setup(
    name='ttktooltip',
    version='1.0',
    description='A tooltip widget for Tkinter',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    py_modules=['ttktooltip'],
    install_requires=[
        'tkinter',  # tkinter is included with Python
    ],
    author='Prashant Mandal',
    author_email='prashant.mandal@example.com',
    url='https://github.com/prashant-mandal/ttktooltip',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.10',
)
