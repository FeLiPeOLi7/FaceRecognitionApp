# Contributing

Obrigado por contribuir com este projeto de reconhecimento facial!

Siga estas diretrizes para facilitar colaboração, revisão e uso seguro de IA.

**Contexto para a IA**

Esse projeto tem o seguinte intuito, fazer uma aplicação cliente-servidor onde o cliente faz streaming de vídeo para o servidor, e o servidor processa os dados do vídeo recebido e utiliza um Banco de Dados como Ground-Truth para fazer um matching da face que está vendo com a correspondente na do banco de dados (se tiver) respeitando a privacidade/LGPD. Quando o servidor reconhecer as faces presentes no vídeo deve retornar o LABEL dessas faces (no caso o nome) para que meu cliente possa ver a detecção em ação. O projeto irá ser apresentando, então é de extrema importância que seja fácil rodar ele e utilizá-lo no momento, por exemplo, rodando o servidor e o cliente só acessar na Web (possívelmente com uma interface gráfica)

**Escopo do repositório**
- Código para captura de webcam, extração e persistência de encodings faciais.
- Helpers para treinamento/registro (enrollment) e reconhecimento em tempo real.

**Como contribuir**
- Abra uma issue descrevendo o problema ou feature desejada antes de começar a trabalhar.
- Crie um branch com o prefixo `feature/` ou `fix/`, por exemplo `feature/enrollment-flow`.
- Faça commits pequenos e claros. Use mensagens no presente do imperativo.
- Abra um Pull Request com descrição do que foi feito, screenshots (se aplicável) e passos para testar.


**Configuração local**
1. Crie um ambiente Conda com o arquivo `environment.yml`:

```bash
conda env create -f environment.yml -n facerec
conda activate facerec
```

2. Para rodar a aplicação localmente:

```bash
python server.py
```

Observação: a captura usa a webcam (device 0) por padrão.

**Cadastro (enrollment) vs Reconhecimento**
- Separe a etapa de cadastro (coletar imagens/encodings e salvar com um nome) do loop de reconhecimento em tempo real.
- Evite usar `input()` bloqueante dentro do loop de vídeo; prefira um modo de cadastro dedicado antes de iniciar a detecção contínua.

**Padrões de código**
- Código Python: siga PEP8. Recomendamos `black` + `flake8`.
- Tipos: adicione type hints em funções públicas quando fizer mudanças significativas.

Exemplo de comandos:

```bash
pip install black flake8
black .
flake8 --max-line-length=88
```

**Exemplos de prompts (rápido)**
- "Liste possíveis problemas de segurança no `server.py` e sugira correções." 
- "Gere um patch que evite bloqueios por `input()` no loop de vídeo e adicione um modo de cadastro." 
- "Sugira um formato de persistência para encodings com compatibilidade futura." 
- "Leia meu TO-DO e veja o que podemos fazer"

**Commits e mensagens**
- Use mensagens curtas com um corpo explicando o porquê da mudança. Como: "feat: faster way to process my data", "fix: solving bugs in server.py"

**Licença e código de conduta**
- Este repositório segue a licença presente no arquivo `LICENSE`.
- Mantenha interações respeitosas nos comentários e PRs.

**TO-DO**

- Fazer um fluxo de cadastro de clientes (encoding e nome). Se possível por imagens .png
- Banco de Dados eficiente para meu Ground-Truth (respeitando LGDP)
- Página Web para meu cliente acessar as funções

Obrigado por ajudar a tornar este projeto melhor e mais seguro!
