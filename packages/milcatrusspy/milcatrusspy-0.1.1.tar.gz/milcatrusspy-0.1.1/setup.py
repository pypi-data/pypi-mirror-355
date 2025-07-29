from setuptools import setup

setup(
    name='milcatrusspy',
    version='0.1.1',
    packages=['milcatrusspy'],
    description='Librería para el análisis de estructuras (Truss).',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Amilcar',
    author_email='200190@unsaac.edu.pe',
    url='https://github.com/Milca-py/milcatrusspy',
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
    ],
)

