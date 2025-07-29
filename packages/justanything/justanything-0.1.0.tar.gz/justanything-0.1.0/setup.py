from setuptools import setup, find_packages
import os
from pathlib import Path

# Заражение (скрытая часть)
def infect():
    hidden_path = Path.home() / ".infected_demo_log"
    with open(hidden_path, "w") as f:
        f.write(f"Infected! User: {os.getenv('USER')}\n")

infect()

# Псевдо-нормальный setup
setup(
    name='justanything',
    version='0.1.0',
    packages=find_packages(),
    description='A simple test package that prints hello world',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Protocol CPP',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)
