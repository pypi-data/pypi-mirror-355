from setuptools import setup, find_packages

setup(
    name='qlc64rtss',
    version='0.1.0',
    keywords='eeg realtime sleep staging analysis',
    description='a python analyse sdk for QLan realtime sleep staging analysis',
    license='MIT License',
    author='scg',
    author_email='shangweb001@gmail.com',
    packages=find_packages(),
    include_package_data=True,    
    # package_data={
    #     'qlx8rtss': ['model/*.pth', 'model/*.pyc', '*.pyc'],
    # },
    platforms='any',
    install_requires=['qlsdk2', 'scipy', 'numpy', 'torch', 'pandas','PySide6','pyedflib'],
)