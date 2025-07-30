from setuptools import setup, find_packages

setup(
    name='cr_package_installable',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
    ],
    description='Création d\'un package installable',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/caplande/cr_package_telechargeable',
    author='Georges Caplande',
    author_email='georges.caplande@gmail.com',
    license='MIT',
)