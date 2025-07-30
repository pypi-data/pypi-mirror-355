from setuptools import setup, find_packages

setup(
    name='Bot-Minecraft',  # Nome que vai aparecer no PyPI (com hífen mesmo)
    version='0.2.0',
    author='Guilherme',
    author_email='h31365202@icloud.com',
    description='Uma biblioteca de bots para Minecraft com mineração e combate automático',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='', # opcional
    packages=find_packages(),
    install_requires=[
        'minecraft==0.1.2',  # Exemplo, coloque os pacotes reais que o seu usa
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)