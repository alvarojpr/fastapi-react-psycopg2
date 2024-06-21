from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

def criar_tabela():
    conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="123", port="5433")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS pessoa (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100),
        email VARCHAR(100),
        file BYTEA
    )""")
    conn.commit()
    cur.close()
    conn.close()

criar_tabela()

app = FastAPI()

origins = [ # Lista de URLs que podem acessar a API
    "http://localhost:5173",
]

app.add_middleware( # Middleware para permitir requisições de origens diferentes
    CORSMiddleware, 
    allow_origins=origins,
    allow_credentials=True, # Permite credenciais
    allow_methods=["*"], # Permite todos os métodos (get, post, delete, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

# Função para conectar ao banco de dados
def conectar_bd():
    conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="123", port="5433")
    return conn # connection

# Função para inserir dados na tabela pessoa
def inserir_pessoa(nome, email, file):
    conn = conectar_bd()
    cur = conn.cursor() # cursor da conexão para executar comandos SQL
    cur.execute("INSERT INTO pessoa (nome, email, file) VALUES (%s, %s, %s)", (nome, email, file))
    conn.commit()
    cur.close()
    conn.close()

@app.post("/upload", status_code=201)
async def criar_pessoa(nome: str = Form(...), email: str = Form(...), file: UploadFile = File(None)):
    try:
        file_data = await file.read() if file else b''
        inserir_pessoa(nome, email, file_data)
        return {"mensagem": "Pessoa criada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir pessoa: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
