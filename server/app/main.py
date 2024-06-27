from typing import Optional # Optional serve para indicar que um argumento pode ser None 
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query # adicionado Query para recuperar o email do usuário e UploadFile para recuperar o arquivo    
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from evtx import PyEvtxParser
from io import BytesIO # BytesIO é um buffer de memória que contém bytes de dados que podem ser lidos e gravados como um arquivo binário

app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], # permitir que qualquer origem acesse a API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def conectar_bd():
    try:
        conn = psycopg2.connect(
            host="localhost",
            dbname="postgres",
            user="postgres",
            password="123",
            port="5433"
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")

def criar_tabela():
    try:
        conn = conectar_bd()
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
    except Exception as e:
        print(f"Erro ao criar tabela: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao criar tabela")

criar_tabela()

def inserir_pessoa(nome, email, file):
    try:
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("INSERT INTO pessoa (nome, email, file) VALUES (%s, %s, %s)", (nome, email, file))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao inserir pessoa: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao inserir pessoa")

@app.post("/upload", status_code=201)
async def criar_pessoa(nome: str = Form(...), email: str = Form(...), file: UploadFile = File(None)):
    try:
        file_data = await file.read() if file else b''
        inserir_pessoa(nome, email, file_data)
        return {"mensagem": "Pessoa criada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir pessoa: {str(e)}")

@app.get("/simplesmenteget", status_code=201)
def recuperarArquivo(email: Optional[str] = Query(None)):
    if not email:
        raise HTTPException(status_code=422, detail="Email is required")

    try:
        conn = conectar_bd()
        cur = conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")

    try:
        cur.execute("SELECT * FROM pessoa WHERE email=%s", (email,))
        pessoa = cur.fetchone()

        if pessoa is None:
            print(f"Nenhuma pessoa encontrada com o email: {email}")
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        arquivo_da_pessoa_em_binario = pessoa[3]

        if arquivo_da_pessoa_em_binario is None:
            print(f"Arquivo da pessoa {email} não encontrado")
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        # Usar BytesIO para criar um objeto de arquivo a partir dos bytes
        arquivo_transformado_em_objeto = BytesIO(arquivo_da_pessoa_em_binario)
        conjunto_de_registros_do_evtx = PyEvtxParser(arquivo_transformado_em_objeto)
        
        # .records_json(): Este método retorna um iterador que gera os registros do arquivo EVTX em formato JSON. Cada registro é um objeto JSON que 
        # representa uma entrada no arquivo EVTX. ---------------------
        # [registro for registro in ...]: é uma forma concisa de criar uma lista. Neste caso, ele está iterando sobre cada registro gerado pelo método 
        # records_json() e adicionando-o à lista registros. ------------------------
        # registros: será uma lista que contém todos os registros do arquivo EVTX em formato JSON.
        # em outras palavras: cria uma lista com cada registro json do arquivo evtx
        registros = [registro for registro in conjunto_de_registros_do_evtx.records_json()]
        print(f"Quantidade de registros recuperados: {len(registros)}")
        return {"registros": registros}

    except Exception as e:
        print(f"Erro ao recuperar arquivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar arquivo: {str(e)}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)



# 200 sucesso, 300 redirecionamento, 400 erro do cliente, 500 erro do servidor
# redirecionamento é quando o servidor diz para o cliente ir para outro lugar