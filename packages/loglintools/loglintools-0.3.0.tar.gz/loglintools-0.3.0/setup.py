from setuptools import setup, find_packages

setup(
    name='loglintools',                     # Название библиотеки
    version='0.3.0',                       # Версия
    packages=['loglintools'],              # Автоматический поиск пакетов
    author='MK',
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
