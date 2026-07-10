<h1 align="center"> <img width="420" height="200" alt="face_recog_banner" src="https://github.com/user-attachments/assets/f1a49f5e-c845-4353-8c19-a5d76f25f1cc" /> </h1>


# Face Recognition Web App (V3.0.1)

Sistema web de reconhecimento facial utilizando uma arquitetura desacoplada com Flask/Sockets no backend e React no frontend, focado em alta performance, componentização e conformidade com a LGPD.

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
├── backend
│   ├── database.py
│   ├── processing.py
│   ├── server.py
│   ├── telemetry
│   └── uploads
├── environment.yml
├── frontend
│   ├── dist
│   ├── eslint.config.js
│   ├── index.html
│   ├── node_modules
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   ├── README.md
│   ├── src
│   └── vite.config.js
├── LICENSE
├── package-lock.json
└── README.md
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

* Sockets

**Frontend (Interface e Controle de Dispositivos)**

* React

* Vite

* CSS Modules

* Socket.IO-Client

* HTML5 Canvas & MediaDevices API

---

## Arquitetura

O sistema utiliza uma arquitetura híbrida:

- Flask (porta 5000) para cadastro biométrico e operações REST.
- Servidor HTTP baseado em sockets nativos (porta 5001) para processamento contínuo de frames em tempo real.

Essa separação reduz o overhead do reconhecimento facial e permite maior controle sobre o pipeline de comunicação.

---

## Configuração do Backend (Flask + SocketIO)
```
# Clone o repositório, crie e ative o ambiente virtual do Conda
conda env create -f environment.yml -n facerec
conda activate facerec

# Navegue até a pasta do backend e execute o servidor
cd backend

# Instale a autoridade certificadora local no seu sistema
mkcert -install

# Gere os certificados válidos apontando para o seu IP Local
# Substitua 'xxx.xxx.xx.x' pelo endereço IP real da sua máquina na rede local
mkcert localhost 127.0.0.1 ::1 xxx.xxx.xx.x

# ou

mkcert localhost 127.0.0.1 ::1

# Execute o Servidor
python server.py
```

---

## Configuração do Frontend (Vite + React)

```
# Acesse o diretório do frontend
cd frontend

# Instale os pacotes e a árvore de dependências
npm install

# Inicie o Host (Cliente)
npm run dev -- --host
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
1. Na tela inicial, selecione a opção Reconhecer Face.
   
2. Clique em Start para iniciar o acesso à webcam.

3. Os frames capturados pelo navegador são convertidos para JPEG/Base64 e enviados periodicamente ao backend através de requisições HTTP para o endpoint /frame.

4. O servidor processa cada frame utilizando o modelo de reconhecimento facial, compara os embeddings detectados com a base de dados cadastrada e identifica possíveis correspondências.

5. O frame anotado com as bounding boxes e os nomes reconhecidos é retornado ao frontend e exibido em tempo real para o usuário.

## Funcionamento

Fluxo do reconhecimento:

```text
       [Frontend Client Space]                     [Backend Processing Core]

         Webcam Media Device
                 │
                 ▼
          Canvas Capture
                 │
                 ▼
         JPEG/Base64 Frame
                 │
                 ▼
        HTTP POST /frame
                 │
                 ├──────────────────────────────► Raw Socket Server
                 │                                      │
                 │                                      ▼
                 │                            Face Recognition Engine
                 │                                      │
                 │                                      ▼
                 │                           Ground-Truth Database
                 │                                      │
                 ▼                                      ▼
      Annotated JPEG Response ◄──────────────── Face Match Result
                 │
                 ▼
          Processed Frame UI
```

---

 ## Possíveis Melhorias Futuras

A arquitetura atual já utiliza um modelo híbrido, combinando Flask para operações REST e um servidor HTTP implementado sobre sockets nativos para o processamento de frames em tempo real. Como evolução futura, o projeto poderá incorporar otimizações adicionais focadas em escalabilidade, desempenho e experiência do usuário.

Algumas melhorias a ser destacadas são: 

- Expansão da camada de telemetria para monitoramento detalhado de latência, throughput, utilização de recursos e capacidade de atendimento concorrente.
  
- Containerização da aplicação utilizando Docker para simplificar a implantação em diferentes ambientes.
  
- Integração com bancos de dados vetoriais especializados para suportar bases biométricas de maior escala.


Essas melhorias visam aumentar a eficiência do sistema, reduzir o consumo de recursos computacionais e ampliar a capacidade de processamento para cenários com maior número de usuários simultâneos.

Além disso, planeja-se integrar melhorias substanciais na experiência do usuário (UX), principalmente se tratando de usuários Mobile.

---

## Observações

* Apenas uma face deve estar presente na imagem de cadastro para evitar ambiguidades no mapeamento vetorial.
* É necessário consentimento para armazenamento de biometria.
* O diretório `uploads/` é utilizado apenas temporariamente, nenhuma imagem fica salvo lá.
* O reconhecimento depende da qualidade da imagem e iluminação.
