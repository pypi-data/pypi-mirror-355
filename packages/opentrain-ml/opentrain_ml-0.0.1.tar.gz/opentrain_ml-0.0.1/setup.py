from setuptools import setup, find_packages

setup(
    name="opentrain-ml",
    version="0.0.1",
    description="Modular and extensible ML training framework",
    author="Shramadeep",
    author_email="shramadeep8@gmail.com",
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    install_requires=[
        "torch>=1.12",
        "torchvision",
        "PyYAML",
        "tqdm",
        "omegaconf",
        "scikit-learn",
        "wandb",        # Optional logging
        "rich",         # Pretty logging
    ],
    entry_points={
        "console_scripts": [
            "opentrain=opentrain.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Operating System :: OS Independent',
    ],
    python_requires=">=3.8",
)
