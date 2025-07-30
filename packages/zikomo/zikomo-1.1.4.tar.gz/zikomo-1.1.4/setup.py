from pathlib import Path
from setuptools import setup, find_packages

_dir = Path(__file__).parent.resolve()
file_path = _dir / 'zikomo/package_info.md'

setup(
    name="zikomo",
    version="1.1.4",
    packages=find_packages(),
    package_data={'zikomo': ['*.html','*.md', '*.txt']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'zikomo=zikomo.__main__:main',
            'mini=zikomo.__main__:main',
            'imran=zikomo.__main__:main',
        ]
    },
    author="Imran A. Shah",
    author_email='imran.shah@zikomosolutions.com',
    description="Zikomo Deployment CLI",
    long_description=open(file_path).read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.11',
    license='Private License',
    classifiers=[
        'License :: Other/Proprietary License',
    ],
)
