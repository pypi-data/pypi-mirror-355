from setuptools import setup, find_packages

setup(
    name='pomodev',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'pomodev=devtimer.__main__:run',
        ],
    },
    author='Dhruv Tiwari',
    description='A Pomodoro CLI timer with Git integration.',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
