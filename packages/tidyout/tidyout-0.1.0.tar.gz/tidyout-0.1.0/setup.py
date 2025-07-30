from setuptools import setup, find_packages 

setup(
    name='tidyout',
    version='0.1.0',
    description='Convert raw LLM outputs into clean, structured JSON',
    author='Your Name',
    packages=find_packages(),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'tidyout=tidyout.cli:main'
        ]
    },
)
