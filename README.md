# Face Recognition Web App (V2.0.0)

Sistema web de reconhecimento facial utilizando uma arquitetura desacoplada com Flask no backend e React no frontend, focado em alta performance, componentização e conformidade com a LGPD.

## Funcionalidades

* **Cadastro Híbrido de Clientes:** Permite o registro de novas faces tanto por upload de arquivos estáticos quanto por captura direta da webcam em tempo real (convertendo o frame do canvas dinamicamente em um payload binário).
* **Armazenamento Seguro:** Extração de embeddings faciais e persistência na base de dados Ground-Truth com tratamento rigoroso de privacidade.
* **Reconhecimento Facial Contínuo:** Loop de vídeo full-duplex transmitido a uma taxa estável de FPS utilizando WebSockets para empurrar strings codificadas em Base64 de baixa latência.
* **Componentização Atômica:** Interface totalmente subdividida em componentes especializados de responsabilidade única e uso de CSS Modules para isolamento completo de escopo estilístico.
* **Conformidade com a LGPD:** Validação obrigatória de consentimento do usuário antes do processamento de dados biométricos

---

## Estrutura do projeto

```text
.
├── backend/
│   ├── database.py
│   └── server.py
├── frontend/
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── assets/
│       ├── components/
│       │   ├── Common/
│       │   ├── Home/
│       │   ├── Recognize/
│       │   └── Register/
│       ├── hooks/
│       └── styles/
├── environment.yml
├── CONTRIBUTING.md
└── LICENSE
```

---

## Tecnologias utilizadas

**Backend (Servidor e API)**

* Python

* Flask

* Flask-SocketIO + Eventlet

* Face Recognition (dlib)

* OpenCV (cv2)

* NumPy

* Pillow (PIL)

**Frontend (Interface e Controle de Dispositivos)**

* React

* Vite

* CSS Modules

* Socket.IO-Client

* HTML5 Canvas & MediaDevices API

---

## Configuração do Backend (Flask + SocketIO)
```
# Clone o repositório, crie e ative o ambiente virtual do Conda
conda env create -f environment.yml -n facerec
conda activate facerec

# Navegue até a pasta do backend e execute o servidor
cd backend
python server.py
```

---

## Configuração do Frontend (Vite + React)

```
# Acesse o diretório do frontend
cd frontend

# Instale os pacotes e a árvore de dependências
npm install

# Inicie o servidor de desenvolvimento
npm run dev
```

---

## Guia de Uso
**Cadastro (Enrollment)**

1. Na tela inicial do sistema, selecione a opção Registrar Face.

2. Insira o nome completo do cliente e marque obrigatoriamente a caixa de autorização legal da LGPD.

3. Escolha a modalidade de envio dos dados biométricos:

    - Upload de Arquivo: Insira um retrato estático isolado contendo apenas um rosto.

    - Capturar via Câmera: Ative a webcam local, posicione-se e clique em Tirar Foto para travar o frame do canvas.

4. Clique em Finalizar Cadastro para disparar a requisição HTTP POST Multipart. O servidor extrairá os encodings, salvará no banco de dados vetorial e retornará o status em tempo real na tela.

**Reconhecimento (Recognition)**

1. No menu principal, clique na opção Reconhecer Face.

2. Clique no botão Start para inicializar o fluxo de hardware e conceder permissão de acesso à webcam.

3. Os frames capturados em background pelo canvas invisível serão serializados em Base64 e despachados via canal WebSocket aberto.

4. O backend receberá os bytes, aplicará o modelo do face_recognition para comparar com os encodings do banco de dados e desenhará a bounding box com o nome detectado diretamente nos frames

## Funcionamento

Fluxo do reconhecimento:

```text
       [Frontend Client Space]                          [Backend Processing Core]
     
         Webcam Media Device
                 │
                 ▼
         Canvas Frame Matrix
                 │
                 ▼
        (Serialized Base64)
                 │
      ┌──────────┴──────────┐
      │   Socket.IO Event   │  ───[WebSocket Channel]───►   Python Server Loop
      └─────────────────────┘                                      │
                                                                   ▼
                                                            Face Recognition
                                                                   │
                                                                   ▼
       Annotated Display UI    ◄───[WebSocket Echo]────  Biometric Ground-Truth Match
```

---

## Observações

* Apenas uma face deve estar presente na imagem de cadastro para evitar ambiguidades no mapeamento vetorial.
* É necessário consentimento para armazenamento de biometria.
* O diretório `uploads/` é utilizado apenas temporariamente, nenhuma imagem fica salvo lá.
* O reconhecimento depende da qualidade da imagem e iluminação.
