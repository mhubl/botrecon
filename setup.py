from setuptools import setup, find_packages
from botrecon import __version__


with open('README.md', 'r') as fp:
    LONG_DESCRIPTION = fp.read()

setup(
    name='botrecon',
    version=__version__,
    description=('Botrecon uses machine learning to locate hosts infected with'
                 'botnets in your network.'),
    long_description_content_type='text/markdown',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    package_data={'botrecon': ['models/*']},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'Click',
        'pandas',
        'numpy',
        'scikit-learn==0.24.1'
    ],
    entry_points="""
        [console_scripts]
        botrecon = botrecon.cli:botrecon
    """,
)
