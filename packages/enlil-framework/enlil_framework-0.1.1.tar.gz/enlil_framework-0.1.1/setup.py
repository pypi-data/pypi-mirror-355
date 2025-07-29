from setuptools import setup, find_packages

setup(
    name="enlil-framework",
    version="0.1.1",
    description="A real frame built on the shoulders of FastAPI framework. Enlil brings back the beauty of structured, modular design - old-school clarity fused with modern performance.",
    author="Goga Patarkatsishvili",
    url="https://github.com/entGriff/enlil",
    project_urls={
        "Source": "https://github.com/entGriff/enlil",
        "Bug Reports": "https://github.com/entGriff/enlil/issues",
        "Documentation": "https://github.com/entGriff/enlil#readme",
    },
    packages=find_packages(),
    package_data={
        "enlil": ["scaffolds/**/*"],
    },
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.115.12,<0.116.0",
        "click>=8.2.1,<9.0.0",
        "tortoise-orm>=0.25.0,<0.26.0",
        "aerich>=0.9.0,<0.10.0",
        "dependency-injector>=4.46.0,<5.0.0",
        "jinja2>=3.1.6,<4.0.0",
        "pydantic>=2.11.5,<3.0.0",
        "pytest>=8.3.5,<9.0.0",
        "httpx>=0.28.1,<0.29.0",
        "factory-boy>=3.3.0,<4.0.0",
        "pytest-asyncio>=0.26.0,<0.27.0",
        "tomlkit>=0.13.2,<0.14.0",
        "uvicorn[standard]>=0.34.2,<0.35.0",
    ],
    extras_require={
        "dev": [
            "ruff~=0.11.12",
            "textual>=3.2.0,<4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "enlil=enlil.cli:cli",
            "enlil-tui=enlil.tui.app:main",
        ],
    },
)