from quart import Quart, render_template
from telethon.sync import TelegramClient, utils
from telethon.tl.types import InputPeerChannel
from datetime import datetime, timedelta
import asyncio
import time
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser,InputMessagesFilterDocument, MessageMediaPhoto, MessageMediaDocument, MessageReactions
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Quart(__name__)


@app.route('/')
async def home():
    return await render_template('index.html')

# Credenciais do Telegram
api_id = os.environ['id']
api_hash = os.environ['hash']
telefone = os.environ['fone']

# Credenciais Google Sheets
arquivo_credenciais ="projeto-final-insper-e3a4847fd379.json"
conteudo_credenciais = os.environ['key']
with open(arquivo_credenciais, mode="w") as arquivo:
    arquivo.write(conteudo_credenciais)
conta = ServiceAccountCredentials.from_json_keyfile_name(arquivo_credenciais)

api = gspread.authorize(conta)
planilha = api.open_by_key("1drW5e4xS54XvuULlR3hLdgQRdSahB4-VJKnq8rb4fJI")
historico = planilha.worksheet("Historico")

# Define o período de tempo
agora = datetime.now()
doze_horas = agora - timedelta(hours=12)

# Função para conectar ao Telegram
async def conectado():
    try:
        client = TelegramClient('session', api_id, api_hash)
        await client.start(telefone)
        await client.connect()

        if not await client.is_user_authorized():
            # Implemente o código para obter código de verificação ou senha
            pass

        return client
    except Exception as e:
        print("Erro durante a conexão com o Telegram:", e)
        return None

# Função que define o tipo de mídia que a mensagem contém
def tipo_midia(message):
    if message.media is not None:
        if isinstance(message.media, MessageMediaPhoto):
            return 'Foto'
        elif isinstance(message.media, MessageMediaDocument):
            if message.media.document.mime_type.startswith('video'):
                return 'Vídeo'
            elif message.media.document.mime_type.startswith('audio'):
                return 'Áudio'
            else:
                return 'Documento'
    return 'Apenas texto'

# Função que define o nome do grupo
def obter_grupo(group_entity):
    nome_grupo = group_entity.title
    return nome_grupo

# Função que mostra o conteúdo da mensagem
def obter_mensagem(message):
    mensagem = message.message
    return mensagem

# Função que para obter o link da mensagem
def obter_link(message):
    return f"https://t.me/c/{message.to_id.channel_id}/{message.id}"

# Função que mostra a data da mensagem
def obter_data(message):
    return message.date.strftime('%d-%m-%Y %H:%M')

# Função que mostra as visualizações da mensagem
def obter_visualizacoes(message):
    return message.views if message.views is not None else 0

# Grupos que serão raspados
grupos = ['@freedomnewsforyou', '@VanLiberdadeOficial', '@circulanarede', '@odespertarreserva', '@selvaeaco']

# Função que processa os grupos, coleta as mensagens das últimas 12 horas e as envia para a planilha
async def processar_grupos(client):
    dados_processados = []
    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        time.sleep(2)
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=5,
            offset_date=doze_horas,
            reverse=True)

        for message in messages:
            nome_grupo = obter_grupo(group_entity)
            mensagem = obter_mensagem(message)
            midia_tipo = tipo_midia(message)
            midia_link = obter_link(message)
            data =  obter_data(message)
            visualizacoes = obter_visualizacoes(message)         
            dados_processados.append((nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes))
            time.sleep(2)
            historico.append_row([nome_grupo, midia_tipo, mensagem, midia_link, data, visualizacoes])

    return dados_processados
    
# Rota para exibir os dados processados
@app.route('/dados')
async def dados():
    async with TelegramClient('session', api_id, api_hash, timeout=10) as client:
        dados_processados = await processar_grupos(client)
        return await render_template('telegram.html', dados=dados_processados)

# Função para mensagens mais vistas
async def get_top_messages(client):
    mais_vistas_grupos = []

    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        time.sleep(2)
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=10,
            offset_date=doze_horas,
            reverse=True)

    
        for message in messages:
            nome_grupo = obter_grupo(group_entity)
            mensagem = obter_mensagem(message)
            midia_tipo = tipo_midia(message)
            midia_link = obter_link(message)
            data = obter_data(message)
            visualizacoes = obter_visualizacoes(message)
            if message.views is not None:
                mais_vistas_grupos.append((nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes))

        mais_vistas_grupos.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
        mais_vistas_grupos[:5]
        print(mais_vistas_grupos)

    return mais_vistas_grupos

# Rota para visualizar as mensagens mais vistas
@app.route('/maisvistas')
async def mais_vistas():
    async with TelegramClient('session', api_id, api_hash, timeout=10) as client:
        mais_vistas_grupos = await get_top_messages(client)
        return await render_template('maisvistas.html', mais_vistas=mais_vistas_grupos)

if __name__ == '__main__':
    app.run()



