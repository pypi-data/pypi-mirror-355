from setuptools import setup, find_packages

setup(
    name='gzusus_image_processing',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Pillow',
    ],
    author='João Vitor',
    description='Pacote simples para processamento de imagens com Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/GzuSus/image-processing-package.git',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
