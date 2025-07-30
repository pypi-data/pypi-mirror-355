from setuptools import setup, find_packages

setup(
    name="genoa",
    version="0.3.1",
    author="MrPsyghost",
    author_email="shivaypuri2000@gmail.com",
    description="GENOA: Genetic Evolutionary Neural Optimization Algorithm — A neural network evolution framework built with PyTorch.",
    # long_description=open("README.md", encoding="utf-8").read(),
    # long_description_content_type="text/markdown",
    # url="https://github.com/MrPsyghost/genoa",
    # project_urls={
    #     "Bug Tracker": "https://github.com/MrPsyghost/genoa/issues",
    #     "Documentation": "https://github.com/MrPsyghost/genoa/wiki",
    # },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        # "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "rich>=13.0.0",
        "matplotlib>=3.10.0"
    ],
    python_requires=">=3.10",
    include_package_data=True,
    # license="MIT",
    keywords=["neural networks", "evolution", "optimizer", "genetic algorithm", "deep learning", "pytorch"],
)
