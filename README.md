# Face Recognition Web App (V1.0.0)

Sistema web de reconhecimento facial utilizando Flask, OpenCV, Face Recognition e Socket.IO.

## Funcionalidades

* Cadastro de pessoas por imagem
* Armazenamento de embeddings faciais no banco de dados com criptografia em repouso (respeitando a LGPD)
* Reconhecimento facial em tempo real
* Streaming da webcam via navegador
* Comunicação em tempo real usando WebSocket

---

## Estrutura do projeto

```text

server.py
database.py

templates/
    index.html
    register.html
    recognize.html

scripts/
    recognize.js

uploads/
```

---

## Tecnologias utilizadas

* Python
* Flask
* Flask-SocketIO
* OpenCV
* face_recognition
* NumPy
* Pillow

---

## Instalação

Crie um ambiente virtual:

```bash
conda env create -f environment.yml -n facerec
conda activate facerec
```

---

## Executando

Inicie o servidor:

```bash
python server.py
```

O sistema ficará disponível em:

```text
http://localhost:5000
```

---

## Uso

### Cadastro

1. Acesse:

```text
http://localhost:5000/register
```

2. Digite um nome

3. Escolha uma imagem contendo apenas um rosto

4. Autorize o processamento biométrico

5. Clique em registrar

---

### Reconhecimento

1. Acesse:

```text
http://localhost:5000/recognize
```

2. Permita acesso à webcam

3. O sistema detectará rostos e exibirá o nome correspondente

---

## Funcionamento

Fluxo do reconhecimento:

```text
Webcam
    ↓
Captura do frame
    ↓
Socket.IO
    ↓
Servidor Flask
    ↓
Face Recognition
    ↓
Busca no banco
    ↓
Retorno do frame processado
    ↓
Exibição no navegador
```

---

## Observações

* Apenas uma face deve estar presente na imagem de cadastro.
* É necessário consentimento para armazenamento de biometria.
* O diretório `uploads/` é utilizado apenas temporariamente, nenhuma imagem fica salvo lá.
* O reconhecimento depende da qualidade da imagem e iluminação.
