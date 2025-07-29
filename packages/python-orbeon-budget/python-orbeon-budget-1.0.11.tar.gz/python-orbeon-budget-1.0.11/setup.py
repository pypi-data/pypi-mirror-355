from setuptools import setup, find_packages


setup(
    name="python-orbeon-budget",
    version="1.0.11",
    packages=find_packages(),
    install_requires=[
        "pillow>=11.1,<11.2",
        "reportlab",
    ],
    extras_require={
        "pycairo": ["reportlab[pycairo]"]
    },
    include_package_data=True,
    package_data={
        "python_orbeon_budget": [
            "contents/*.png",
        ],
    },
    description="Uma biblioteca leve e independente para gerar orçamentos padronizados em formato PDF A4 a partir de um dicionário (context).",
    author="Edu Fontes",
    author_email="eduramofo@gmail.com",
    url="https://github.com/getorbeon/python-orbeon-budget",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
