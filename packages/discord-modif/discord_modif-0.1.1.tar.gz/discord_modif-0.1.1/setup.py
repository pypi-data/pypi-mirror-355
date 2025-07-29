from setuptools import setup, find_packages

setup(
    name="discord-modif",
    version="0.1.1",
    author="Diabriek",
    description="Lib using discord.py for configure your server, with this lib use discord.py is very easier",
    packages=find_packages(),
    install_requires=[
        "discord.py"
    ],
    python_requires=">=3.10",
)
