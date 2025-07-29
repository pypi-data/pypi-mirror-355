from setuptools import setup, find_packages

setup(
    name='ceasar-toolkit',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'colorama',
        'PyPDF2',
    ],
    entry_points={
        'console_scripts': [
            'ceasar=ceasar.main:main',  # maps "ceasar" CLI to your main.py
        ]
    },
    author='Hounaar',
    description='Caesar Cipher CLI Toolkit for encryption, PDF, and folder protection',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.8',
)
