from setuptools import setup, find_packages

setup(
    name='liquipediarl',
    version='1.0.5',
    description='Liquipedia Rocket League API Wrapper',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Kian Mortimer',
    author_email='kmortimer@proton.me',
    url='https://github.com/kianmortimer/liquipediarl',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.7',
)
