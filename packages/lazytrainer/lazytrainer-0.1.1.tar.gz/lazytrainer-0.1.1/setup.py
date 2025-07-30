from setuptools import setup, find_packages

setup(
    name="lazytrainer",
    version="0.1.1",
    author="Mr. Phantom",
    description="Lazy ML: Because training models shouldn't need more energy than your morning coffee.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),  
    install_requires=[
        "pandas",
        "numpy",
        "scikit-learn",
        "matplotlib",
        "joblib",
        "tqdm"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.7',
)
