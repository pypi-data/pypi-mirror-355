from setuptools import setup, find_packages

setup(
    name="discord-modif",
    version="0.1.0",
    author="TonNom",
    description="Librairie pour modifier des serveurs Discord",
    packages=find_packages(),
    install_requires=[
        "discord.py"
    ],
    python_requires=">=3.8",
)
