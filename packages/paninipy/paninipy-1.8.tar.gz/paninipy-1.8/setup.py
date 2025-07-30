from setuptools import setup, find_packages, Extension

setup(
    name='paninipy',
    version='1.8',
    description='Package of Algorithms for Nonparametric Inference with Networks in Python',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://paninipy.readthedocs.io/en/latest/index.html',
    author='Baiyue He, Alec Kirkley',
    author_email='baiyue.he@connect.hku.hk, akirkley@hku.hk',
    license='The MIT License',
    project_urls={
        "Documentation": "https://paninipy.readthedocs.io/en/latest/index.html",
        "Source": "https://paninipy.readthedocs.io/en/latest/index.html"
    },
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",    
        "pandas>=2.2",
        "scipy>=1.10",
        "ray>=2.40.0"
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["paper = paper.cli:main"]},
)
