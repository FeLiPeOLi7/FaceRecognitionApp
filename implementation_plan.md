# Plano de Implementação: SQLite + sqlite-vec para Ground-Truth (LGPD)

Este plano descreve como migraremos o armazenamento de encodings faciais e nomes para um banco de dados SQLite unificado usando a extensão moderna de busca vetorial **`sqlite-vec`**, respeitando a LGPD com criptografia em repouso e consentimento do usuário.

## User Review Required

> [!IMPORTANT]
> **Instalação Sem Sudo:** Usaremos o comando `pip install sqlite-vec` no ambiente Conda ativo. Não é necessária nenhuma permissão de administrador (`sudo`).
> 
> **Segurança / Criptografia dos Nomes (LGPD):** Criptografaremos o nome do usuário antes de salvá-lo no SQLite. Usaremos um algoritmo de cifra de fluxo CTR seguro baseado puramente em bibliotecas nativas do Python (`hashlib` e `hmac`), sem dependências externas adicionais de criptografia. A chave privada será gerada e salva no arquivo local `db_key.key` com permissão restrita.
> 
> **Deleção Atômica (LGPD):** Com o `sqlite-vec`, quando o usuário solicitar o "Direito ao Esquecimento" (exclusão de dados), deletaremos o registro cadastral e o vetor biométrico simultaneamente em uma única transação SQL.

## Proposed Changes

---

### [Component] Vector Database Module (`database.py`)

Criaremos o módulo centralizado de banco de dados e criptografia.

#### [NEW] [database.py](file:///home/slower/Documents/FaceRecognitionApp/database.py)
- **Carregamento da Extensão:**
  ```python
  import sqlite3
  import sqlite_vec

  conn = sqlite3.connect("faces.db")
  conn.enable_load_extension(True)
  sqlite_vec.load(conn)
  ```
- **Esquema das Tabelas (Relacional):**
  1. **Tabela de Usuários (Padrão SQL):**
     ```sql
     CREATE TABLE IF NOT EXISTS users (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         name_encrypted BLOB NOT NULL,
         consent_given INTEGER NOT NULL DEFAULT 1,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```
  2. **Tabela de Vetores (Virtual do sqlite-vec):**
     ```sql
     CREATE VIRTUAL TABLE IF NOT EXISTS vec_faces USING vec0(
         user_id INTEGER PRIMARY KEY,
         encoding float[128]
     );
     ```
- **Criptografia Simétrica nativa (CTR-mode com PBKDF2/HMAC-SHA256):**
  - Criptografa o nome do usuário antes de salvar e descriptografa no momento do match.
- **Funções Principais:**
  - `init_db()`: Cria as tabelas e carrega a extensão.
  - `save_face(name, encoding_vector, consent_given)`:
    1. Insere o usuário na tabela `users` e obtém o `user_id`.
    2. Converte o vetor NumPy (128 floats) para `float32` binário.
    3. Insere o vetor na tabela virtual `vec_faces`.
  - `search_face(query_vector)`:
    1. Converte o vetor de busca para `float32` binário.
    2. Executa a query vetorial indexada no disco:
       ```sql
       SELECT user_id, distance 
       FROM vec_faces 
       WHERE vec_search(encoding, ?) 
       LIMIT 1;
       ```
    3. Se encontrar um resultado com distância menor que o limiar (ex: 0.6), busca o nome criptografado em `users`, descriptografa-o e retorna o ID, o Nome e a distância.
  - `delete_user_by_name(name)`:
    - Decripta e compara os nomes no banco. Ao achar a linha correspondente, deleta o usuário de `users` e `vec_faces` de forma atômica (LGPD).

---

### [Component] Server Adaptation (`server.py`)

Modificar o loop de vídeo para usar o novo banco.

#### [MODIFY] [server.py](file:///home/slower/Documents/FaceRecognitionApp/server.py)
- Remover as funções antigas `save_encodings`, `load_encodings` e `get_next_filename`.
- Na função `main()`, inicializar o banco: `database.init_db()`.
- Substituir a leitura sequencial em memória do NumPy por chamadas rápidas a `database.search_face(face_encoding)` para cada rosto detectado na tela.
- Atualizar a lógica de cadastro no terminal:
  1. Perguntar explicitamente o consentimento da LGPD:
     `Você consente com o armazenamento e processamento de sua biometria facial nos termos da LGPD? (s/n): `
  2. Se aceito, solicitar o nome e chamar `database.save_face(name, face_encoding, consent_given=True)`.

---

## Plan de Verificação

### Testes Manuais & Funcionais
1. **Instalação:** Executar `pip install sqlite-vec` e rodar um script rápido para verificar se a extensão carrega sem erros.
2. **Criação do Banco:** Validar a criação do arquivo `faces.db` e do arquivo de chave `db_key.key` ao rodar a inicialização.
3. **Fluxo de Consentimento:** Cadastrar uma pessoa pela câmera e verificar se o prompt de consentimento bloqueia/permite o cadastro devidamente.
4. **Verificação de Busca:** Executar a detecção em tempo real e confirmar se o nome do usuário cadastrado aparece na tela de forma correta e se desconhecidos continuam aparecendo como "Unknown".
5. **Verificação de Criptografia:** Abrir o arquivo `faces.db` com um visualizador SQLite comum e comprovar que os nomes estão ilegíveis (criptografados).
