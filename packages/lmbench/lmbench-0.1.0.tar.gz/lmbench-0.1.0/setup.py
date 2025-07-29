from setuptools import setup

setup(
    name='lmbench',
    version='0.1.0',
    py_modules=['cli'],
    entry_points={
        'console_scripts': [
            'lmbench=cli:main',
        ],
    },
    install_requires=[
        'torch',
    ],
    python_requires='>=3.8',
)
