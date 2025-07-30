from setuptools import setup, find_packages

setup(
    name='beta_algoWalk',
    version='1.0.0',
    description='A helpful library for developers and learners to understand the working of algorithms and data '
                'structures.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='@Kasturing',
    url='https://github.com/Kasturing/kasturing_lib',
    license='Apache Software License 2.0',
    packages=find_packages(),
    install_requires=[
        "numpy>=1.18",
        "pandas>=1.0",
        "plotly>=5.0"
    ],
    python_requires='>=3.7',
)
