from setuptools import setup, find_packages

setup(
    name="ishne_to_csv",
    version="1.1",
    description="Convert ISHNE ECG Holter files to timestamped CSV format",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Saurabh Barthwal",
    packages=find_packages(),
    install_requires=["pandas", "tqdm"],
    entry_points={
        'console_scripts': [
            'ishne_to_csv = ishne_to_csv.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires='>=3.6',
)
