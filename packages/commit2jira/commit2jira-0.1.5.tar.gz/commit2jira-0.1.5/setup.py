from setuptools import setup, find_packages

setup(
    name='commit2jira',
    version='0.1.5',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['click'],
entry_points={
    'console_scripts': [
        'commit2jira=commit2jira.cli:main',
    ],
},


    author='Your Name',
    description='Commit to Jira Hook',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
