from setuptools import setup, find_packages

setup(
    name="aura_connect",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "eclipse-zenoh==1.3.3",
    ],
    description="A simplified wrapper around the Zenoh SDK for pub/sub and request-reply patterns",
    author="AuraSim Team",
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
