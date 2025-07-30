from setuptools import setup, find_packages

setup(
    name="ghup-whatsapp",
    version="0.1.0",
    description="Python SDK para integração com a API de WhatsApp da Gupshup",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Casaroli Fabio",
    author_email="fabiocasarolij@gmail.com",
    url="https://github.com/casarolifabio/gupshup-whatsapp",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat"
    ],
    include_package_data=True,
)
