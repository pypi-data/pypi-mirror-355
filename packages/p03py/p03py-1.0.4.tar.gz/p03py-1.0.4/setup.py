from setuptools import setup, find_packages

setup(
    name='p03py',
    version='1.0.4',
    author='Ronei Toporcov',
    author_email='toporcov@hotmail.com',
    description='Python library for reading industrial scales using the P03 protocol.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/roneitop/p03py',
    packages=find_packages(include=["p03py", "p03py.*"]),
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    license='MIT',
)
