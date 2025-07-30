from setuptools import setup, find_packages

setup(
    name='analyzer',
    version='0.1.0',
    py_modules=['cli'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'opencv-python',
        'numpy',
        'toml',
        'scikit-learn'
    ],
    entry_points={
        'console_scripts': [
            'analyzer = analyzer.cli:cli',
        ],
    },
)