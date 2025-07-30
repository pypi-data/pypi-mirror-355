from setuptools import setup, find_packages

setup(
    name="metaidigitcv",
    verbose=True,
    version="0.1.11",
    author="SUHAL SAMAD",
    author_email="samadsuhal@gmail.com",
    description="computer vision and machine learning library",
    long_description=open("README.md", encoding="utf-8").read(),  # Specify UTF-8
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'metaidigit=metaidigitcv.main:main',
        ],
    },
)
