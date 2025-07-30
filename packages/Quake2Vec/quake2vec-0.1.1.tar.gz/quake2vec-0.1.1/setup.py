from setuptools import setup

setup(
    name="Quake2Vec",
    version="0.1.1",
    long_description="Quake2Vec",
    long_description_content_type="text/markdown",
    packages=["quake2vec"],
    install_requires=["numpy",  "h5py", "matplotlib", "pandas"],
)
