import setuptools


setuptools.setup(
    name="nlkt",  # Replace with your package name
    version="4.0.1",           # Initial version
    author="CrypticX",
    author_email="your.email@example.com",
    description="A short description of your package",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "gensim==4.3.3",
        "scipy==1.13.1",
        "numpy==1.26.4",
        "hmmlearn==0.3.3",
        "keras==3.9.0",
        "pandas==2.2.3",
        "sklearn-crfsuite==0.5.0"
    ],
)