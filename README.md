# FruityFur Bot (FFBOT)

| 🇧🇷 Português | 🇺🇸 English |
|---|---|
| O **FFBot** é um bot que auxilia furmeets brasileiros a agendar eventos e publicá-los de forma automatizada, para que as pessoas saibam quando e onde estão acontecendo furmeets ou eventos da furry fandom brasileira.<br><br>Esse bot pode ser clonado e adaptado para as necessidades de outros países, ele foi feito como uma ferramenta para a comunidade furry. Caso queiram sugerir alterações e melhorias, estou à disposição! | **FFBot** is a bot that helps Brazilian furmeets schedule events and publish them automatically, so people know when and where furmeets or events from the Brazilian furry fandom are happening.<br><br>This bot can be cloned and adapted to the needs of other countries, as it was made as a tool for the furry community. If you'd like to suggest changes and improvements, feel free to reach out! |

## Features / Funcionalidades

| 🇧🇷 Português | 🇺🇸 English |
|---|---|
| **📨 /FFPost**<br>Use essa função para criar o evento.<br><br>Crie um post em seu grupo contendo as informações do evento;<br><br>Responda a mensagem do evento com `/FFPost` ou envie o post na DM do bot para agendar a publicação do evento pelo bot;<br><br>O bot irá solicitar a data do evento e enviará o post para ser aprovado! | **📨 /FFPost**<br>Use this function to create the event.<br><br>Create a post in your group containing the event information;<br><br>Reply to the event message with `/FFPost` or send the post to the bot's DM to schedule the event publication through the bot;<br><br>The bot will ask for the event date and send the post for approval! |
| **📅 /FFThisMonth**<br>Use essa função para mostrar os eventos do mês atual publicados pelo bot. | **📅 /FFThisMonth**<br>Use this function to display the current month's events published by the bot. |
| **🗑️ /FFRemove**<br>Responda a mensagem original do evento com este comando para removê-lo do canal e do registro. | **🗑️ /FFRemove**<br>Reply to the original event message with this command to remove it from the channel and the record. |
| **⛔️ /cancel**<br>Cancela a função de criação de evento. | **⛔️ /cancel**<br>Cancels the event creation function. |
| **🏓 /FFPing**<br>Verifica se o bot está online e mostra a versão atual. | **🏓 /FFPing**<br>Checks if the bot is online and shows the current version. |

## Notas / Notes

| 🇧🇷 Português | 🇺🇸 English |
|---|---|
| ⚠️ `/FFPost` só funciona em grupos ou grupos de canais. | ⚠️ `/FFPost` only works in groups or channel groups. |
| ⚠️ `/FFThisMonth` só pode ser usado em grupo por administradores; usuários podem chamar essa mensagem pela DM do bot. | ⚠️ `/FFThisMonth` can only be used in a group by administrators; users can call this message via the bot's DM. |
| ⚠️ Apenas administradores do grupo podem usar as funções. | ⚠️ Only group administrators can use the functions. |

## Setup

| 🇧🇷 Português | 🇺🇸 English |
|---|---|
| 1. Crie um arquivo `.env` com as variáveis necessárias, baseando-se em `config.py` | 1. Create a `.env` file with the necessary variables, based on `config.py` |
| 2. Instale as dependências: `pip install python-telegram-bot python-dotenv` (ou siga o `requirements.txt`) | 2. Install the dependencies: `pip install python-telegram-bot python-dotenv` (or follow `requirements.txt`) |
| 3. Valide a linguagem que você quer utilizar pelos dicionários, ou crie seu dicionário personalizado com a sua língua nativa. | 3. Validate the language you want to use through the dictionaries, or create your own custom dictionary with your native language. |
| 4. Rode com `python run.py` (ou `run_local.py`) | 4. Run with `python run.py` (or `run_local.py`) |

---

**Versão atual / Current version:** 3.1.1 (Apricot-Pie)
