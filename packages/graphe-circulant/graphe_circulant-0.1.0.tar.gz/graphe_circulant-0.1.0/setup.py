from setuptools import setup, find_packages

setup(
    name='graphe_circulant',
    version='0.1.0',
    author='lakrakar_labibi',
    author_email='lakrakarouafaa@email.com',
    description='Package pour le calcul de diamètres de graphes circulants',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'numpy',
        'networkx',  # si tu l’utilises
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
)
