from setuptools import setup, find_packages

# Full MIT License text
MIT_LICENSE_TEXT = """
MIT License

Copyright (c) 2023 Manas Pathak

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

setup(
    name='Mapicx',
    version='0.1.0',
    description='A lightweight ANN library from scratch using NumPy',
    author='Manas Pathak',
    author_email='manaspathak1711@gmail.com',
    license='MIT',
    license_text=MIT_LICENSE_TEXT,  # Embedded license text
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'nnfs',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    # Prevent license file inclusion
    license_files=[],
    include_package_data=False,
)