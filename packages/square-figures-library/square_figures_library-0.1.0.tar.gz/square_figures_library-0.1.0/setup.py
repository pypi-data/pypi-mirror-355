from setuptools import setup, find_packages


setup(
    name='square_figures_library',
    version='0.1.0',
    author='Акчурин Лев',
    author_email='levisserena@yandex.ru',
    description='Подсчет площади геометрических фигур.',
    long_description=open('Readme.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/levisserena/square_figures_library',
    packages=find_packages(exclude=['tests']),
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)
