from setuptools import setup, find_packages

setup(
    name='go-ssh',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'gossh=go_ssh.__main__:main'
        ]
    },
    author='your-name',
    description='Smart fuzzy SSH connector using ~/.ssh/config',
    python_requires='>=3.6',
)