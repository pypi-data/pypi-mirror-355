from setuptools import setup, find_packages

setup(
    name="evolvishub-alertmanager",
    version="0.1.1",
    author="Alban Maxhuni, PhD",
    author_email="a.maxhuni@evolvis.ai",
    description="A flexible alert management system with SQLite backend",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/evolvisai/evolvishub-alertmanager-adapter",
    packages=find_packages(where="."),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "sqlalchemy>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "alertmanager=alertmanager.cli:main",
        ],
    },
    license="MIT",
    license_files=("LICENSE",),
) 