from setuptools import setup, find_packages

setup(
    name='snqs-kpm',
    version='0.1.9',
    packages=find_packages(exclude=["tests*", "docs*"]),
    install_requires=[
    ],
    author='Wei Liu',
    author_email='liuwei.chem.phys@gmail.com',
    description='Scalable Neural Quantum State based Kernel Polynomial Method for Optical Properties from the First Principle',
    url='https://github.com/Weitheskmt/sNQS-KPM',

    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',

)