# 1. Crie o ambiente virtual (se quiser)
py -m venv .venv
.\.venv\Scripts\activate

# 2. Instale as dependências (sem Pillow agora)
py -m pip install -r requirements.txt

# 3. Popule o banco de dados
py seed.py

# 4. Execute o projeto
py run.py