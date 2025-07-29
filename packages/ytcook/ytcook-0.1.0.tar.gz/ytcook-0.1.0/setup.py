from setuptools import setup, find_packages

setup(
    name='ytcook', 
    version='0.1.0', 
    author='Ahmed', 
    author_email='support@ton-service.info', 
    description='Auto cookie extractor for YouTube using browser-cookie3',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ToN-Service/ytcook',
    packages=find_packages(),
    install_requires=[
        'browser-cookie3',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
