from setuptools import find_packages, setup

with open('README.md', encoding='utf-8') as readme:
    long_description = readme.read()

setup(
    name='pygclock',
    version='1.1.0',
    description='PyGClock, simple clock library like Clock on PyGame.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='azzammuhyala',
    license='MIT',
    python_requires='>=3.5',
    packages=find_packages(),
    include_package_data=True,
    keywords=['clock', 'simple clock', 'pygame clock', 'pygclock', 'simple pygame clock'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)