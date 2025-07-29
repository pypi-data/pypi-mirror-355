from setuptools import setup, find_packages

setup(
    name='gitanalytics',
    version='0.0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'click>=8.1.7',
        'gitpython>=3.1.41',
        'openai>=1.12.0',
        'jinja2>=3.1.3',
        'rich>=13.7.1',
        'pydantic>=2.6.3',
        'pydantic-settings>=2.2.1',
        'python-dotenv>=1.0.1',
        'requests>=2.31.0',
        'psutil>=5.9.8',
    ],
    entry_points={
        'console_scripts': [
            'gitanalytics = gitanalytics.cli:main',
        ],
    },
)