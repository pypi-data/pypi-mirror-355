# setup.py (Localizado na raiz do projeto pyexops/)

import setuptools
import os
import re

# --- Função para extrair a versão de src/pyexops/__init__.py ---
def get_version():
    """
    Lê a versão de src/pyexops/__init__.py sem importar o pacote
    para evitar problemas de dependência durante a instalação.
    """
    init_py_path = os.path.join(os.path.dirname(__file__), 'src', 'pyexops', '__init__.py')
    with open(init_py_path, 'r') as f:
        init_py = f.read()
    
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", init_py, re.MULTILINE)
    if match:
        return match.group(1)
    else:
        raise RuntimeError("Não foi possível encontrar a string da versão em src/pyexops/__init__.py")

# Use a versão extraída de src/pyexops/__init__.py
VERSION = get_version()

# --- Obtém a descrição longa do arquivo README.md ---
# Assume que README.md está no mesmo diretório que setup.py
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# --- Lê as dependências do requirements.txt ---
# Garante que setup.py e requirements.txt estejam sincronizados para as dependências de runtime.
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
install_requires = []
if os.path.exists(requirements_path):
    with open(requirements_path, 'r', encoding='utf-8') as f:
        install_requires = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    print("Aviso: requirements.txt não encontrado. Usando uma lista padrão de dependências essenciais para setup.")
    # Fallback se requirements.txt estiver faltando (não ideal para um lançamento)
    install_requires = [
        "numpy>=1.20",
        "matplotlib>=3.4",
        "scipy>=1.7",
        "dask>=2023.0.0",
        "distributed>=2023.0.0",
    ]

# --- Dependências opcionais (para desenvolvimento, teste, documentação, etc.) ---
extras_require = {
    "cuda": ["dask-cuda>=2023.0.0"], # Para aceleração por GPU com Dask
    "dev": [ # Dependências de desenvolvimento (para desenvolvimento local, não para o pacote distribuído)
        "pytest>=6.0",
        "flake8>=3.9",
        "black>=21.0b0",
        "ipykernel", # Para executar notebooks de exemplo
        "jupyterlab",
        "twine", # Para uploads para PyPI
        "wheel", # Para construir wheels
        "build" # Para construir distribuições
    ],
    "docs": [ # Dependências específicas para a documentação
        "sphinx>=4.0",
        "sphinx-rtd-theme>=1.0",
        "nbsphinx>=0.8", # Para integrar notebooks à documentação do Sphinx
        "ipykernel", # nbsphinx precisa disso para executar notebooks
    ],
    "test": [ # Dependências específicas para testes
        "pytest>=6.0",
        # Adicione quaisquer outras dependências específicas de teste que possam ser necessárias
    ]
}
# Combina todas as extras para facilitar a instalação de todos os componentes opcionais
extras_require["all_extras"] = sum(extras_require.values(), [])


setuptools.setup(
    name="pyexops",  # Nome do pacote como aparecerá no PyPI
    version=VERSION, # Usa a versão obtida de get_version()
    author="Your Name or Organization", # <-- SUBSTITUA
    author_email="your.email@example.com", # <-- SUBSTITUA
    description="Um simulador Python de Sistemas Exoplanetários para curvas de luz e velocidades radiais.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/pyexops",  # URL do seu repositório GitHub (SUBSTITUA)
    project_urls={ # URLs úteis adicionais
        "Bug Tracker": "https://github.com/your_username/pyexops/issues", # <-- SUBSTITUA
        "Documentation": "https://pyexops.readthedocs.io/", # <-- SUBSTITUA (e.g., URL do ReadTheDocs)
        "Source Code": "https://github.com/your_username/pyexops", # <-- SUBSTITUA
    },
    # package_dir informa ao setuptools que o código do pacote (para o nome de importação 'pyexops')
    # está localizado no diretório 'src/'. A chave de string vazia '' significa
    # "o pacote raiz e todos os seus subpacotes".
    package_dir={'': 'src'},
    # packages encontra todos os pacotes dentro do diretório especificado pelo valor de package_dir para ''.
    # Assim, ele procurará dentro de 'src/' por um diretório chamado 'pyexops' (e seus subpacotes).
    packages=setuptools.find_packages(
        where='src',
        # Exclui diretórios que não são pacotes de código da pasta 'src/' se houver
        # (embora geralmente tests/examples/docs estejam fora de src/ no layout src-layout)
        exclude=['tests*', 'examples*', 'docs*']
    ),
    classifiers=[
        "Development Status :: 3 - Alpha",  # Status de desenvolvimento (3 - Alpha, 4 - Beta, 5 - Stable)
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",  # Use sua licença real
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12", # Adicione versões mais recentes se suportadas
        "Natural Language :: English", # A língua principal do código e documentação
    ],
    python_requires='>=3.8', # Versão mínima do Python necessária
    install_requires=install_requires,
    extras_require=extras_require,
    keywords="exoplanets transit simulation light curve radial velocity photometry dask astronomy",
)