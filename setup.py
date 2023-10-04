from setuptools import find_packages, setup

install_requires = [
        'proteinshake',
        'scikit-learn'
]

setup(
    name='shake_release',
    description='Release builder for Proteinshake.',
    author = "Tim Kucera, Carlos Oliver, Dexiong Chen, Karsten Borgwardt",
    author_email = "kucera@biochem.mpg.de",
    keywords = ['bioinformatics',
                'deep-learning',
                'computational-biology',
                'macromolecular-structure'],
    python_requires='>=3.7',
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,
)
