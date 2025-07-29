from setuptools import setup, find_packages

setup(
    name="base-system-api", 
    version="0.1.0",  # Versão inicial
    author="Raian Barbosa",
    author_email="raianpbstudio@gmail.com",
    description="Uma ferramenta CLI para gerar estruturas e código para projetos API",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/seuusuario/fastapi-cli-bs",  # Substitua pelo link do repositório
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "passlib",
        "python-jose",
        "alembic",
        "click",
        "jinja2"
    ],
    entry_points={
        "console_scripts": [
            "bs=bs_cli.cli:cli",  # Registra o comando `bs` no terminal
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
