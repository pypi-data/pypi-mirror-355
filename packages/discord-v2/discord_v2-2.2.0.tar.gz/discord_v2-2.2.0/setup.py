from setuptools import setup, find_packages

setup(
    name="discord_v2",  # nom unique sur PyPI !
    version="2.2.0",
    author="MJVhack",
    author_email="duc.kalipython@gmail.com",
    description="A powerful discord lib and easy; documentation: https://mjvhack.github.io/documantation/discord_v2.html",
    url="https://github.com/MJVhack/discord.py_v2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "discord.py",  
    ],
)

