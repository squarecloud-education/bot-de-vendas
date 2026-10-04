<div align="center">
  <img alt="Square Cloud Banner" src="https://cdn.squarecloud.app/png/github-readme.png">
</div>

> 📌 **Note:** This README is written in Portuguese because this project was created as part of a YouTube tutorial in Portuguese.

<h1 align="center">sales-bot</h1>
<p align="center">Um bot de vendas completo para Discord criado com <a href="https://discordpy.readthedocs.io/" target="_blank">discord.py</a> e a <a href="https://www.mercadopago.com.br/developers" target="_blank">API do Mercado Pago</a>.</p>

---

Este projeto é um **bot de vendas completo** para Discord desenvolvido durante uma série de vídeos no canal do YouTube da **Square Cloud**, demonstrando como construir um sistema de vendas profissional usando **discord.py** e a **API do Mercado Pago**, com pagamento via Pix.

A série de vídeos que originou este projeto está disponível no YouTube:
https://youtu.be/C8ZBov6lQl0

---

## ☁️ Como hospedar na Square Cloud

Nunca usou a Square Cloud? Siga os passos abaixo, na ordem: você vai criar uma conta, escolher um plano, criar o bot no Discord, pegar a chave do Mercado Pago e enviar o projeto.

### 1️⃣ Crie sua conta na Square Cloud

Cadastre-se na [página de cadastro da Square Cloud](https://squarecloud.app/pt-br/signup) com o seu e-mail.

### 2️⃣ Escolha um plano

A hospedagem na Square Cloud precisa de um plano ativo, e o envio do passo 6 pede um, então escolha agora.

Este bot usa só **256 MB de RAM**: o **[plano Hobby](https://squarecloud.app/pt-br/pricing)** é suficiente e ainda sobra espaço para outros bots. Compare todos os planos e preços na [página de planos](https://squarecloud.app/pt-br/pricing).

### 3️⃣ Crie o bot no Discord

1. No [Discord Developer Portal](https://discord.com/developers/applications), clique em **New Application** e dê um nome ao bot.
2. Na aba **Bot**, clique em **Reset Token** e copie o token. Guarde-o em segredo: ele controla o seu bot.
3. Na mesma aba, em **Privileged Gateway Intents**, ative **Presence Intent**, **Server Members Intent** e **Message Content Intent**.
4. Convide o bot para o seu servidor: em **OAuth2 > URL Generator**, marque `bot` e `applications.commands`, escolha as permissões e abra o link gerado.

### 4️⃣ Pegue a chave do Mercado Pago

No [painel de desenvolvedores do Mercado Pago](https://www.mercadopago.com.br/developers/panel/app), crie uma aplicação e copie o **Access Token** das credenciais de produção. É com ele que o bot gera as cobranças Pix.

### 5️⃣ Prepare o projeto

1. No topo desta página, clique em **Code > Download ZIP** e extraia o arquivo.
2. Abra a pasta extraída, selecione **todos os arquivos dentro dela** e compacte-os em um novo `.zip`. Compacte os arquivos, não a pasta: o `squarecloud.app` precisa ficar na raiz do zip.

### 6️⃣ Envie para a Square Cloud

1. Acesse a [página de upload da Square Cloud](https://squarecloud.app/pt-br/dashboard/new).
2. Selecione a opção de **zip** e envie o arquivo que você criou.
3. Abra **Configuração avançada** e adicione as variáveis de ambiente:
   - `BOT_TOKEN`: o token do bot (passo 3)
   - `MP_TOKEN`: o Access Token do Mercado Pago (passo 4)
   - `CARGO_GESTOR_ID`: o ID do cargo que pode gerenciar os produtos
   - `CANAL_LOJA_ID`: o ID do canal da loja
4. Clique em **Deploy**.

![Enviando um projeto para a Square Cloud](https://cdn.squarecloud.app/docs/articles/dashboard/uploading.gif)

> 💡 **Como copiar um ID no Discord:** ative o **Modo de desenvolvedor** em **Configurações > Avançado**, clique com o botão direito no cargo ou canal e escolha **Copiar ID**.

Os produtos ficam em um banco SQLite (`database.db`) dentro da própria aplicação, sem precisar de outro serviço.

### 7️⃣ Teste o bot

Com o cargo de `CARGO_GESTOR_ID`, use `/gerenciar` para cadastrar os produtos e envie `!mostrar_produtos` no canal da loja para publicar a vitrine. Se o bot não responder, abra a aplicação no [dashboard da Square Cloud](https://squarecloud.app/pt-br/dashboard) e confira os logs.

📖 Mais detalhes no [guia de bots do Discord](https://docs.squarecloud.app/pt-br/tutorials/bots/discord) da documentação da Square Cloud.

---

## 💻 Rodando no seu computador

1. Instale as dependências: `pip install -r requirements.txt`
2. Preencha as variáveis no arquivo `.env`.
3. Rode o bot: `python main.py`

Requer Python 3.10 ou mais recente.
