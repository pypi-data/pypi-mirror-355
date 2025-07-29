from setuptools import setup, find_packages

setup(
    name='crackpass',
    version='1.0.0',
    author='Bhavika Nagdeo',
    author_email='bhavikanagdeo83@gmail.com',
    description='A password strength analyzer using real-world cracking techniques.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/cracking-bytes/Crack-Pass',
    project_urls={
        'Bug Tracker': 'https://github.com/cracking-bytes/Crack-Pass/issues',
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
    'crackpass': ['wordlists/*'],
    },

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'crackpass = crackpass.__main__:main',
        ],
    },
    python_requires='>=3.6',
)
