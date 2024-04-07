from quart import Quart, render_template
from telethon.sync import TelegramClient, utils
from telethon.tl.types import InputPeerChannel
from telethon.sessions import StringSession
from datetime import datetime, timedelta
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
def subtrair_horas(n_horas):
    agora = datetime.now()
    resultado = agora - timedelta(hours=n_horas)
    return resultado

seis_horas = subtrair_horas(6)
doze_horas = subtrair_horas(12)

string = os.environ['string']
async def conecta():
    client = TelegramClient(StringSession(string), api_id, api_hash)
    await client.start(telefone)
    await client.connect()
    return client
    

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
            limit=30,
            offset_date=seis_horas,
            reverse=True)

        for message in messages:
            nome_grupo = obter_grupo(group_entity)
            mensagem = obter_mensagem(message)
            midia_tipo = tipo_midia(message)
            midia_link = obter_link(message)
            data =  obter_data(message)
            visualizacoes = obter_visualizacoes(message)         
            dados_processados.append((nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes))
 
    return dados_processados

async def enviar_para_planilha(dados_processados):
    for dado in dados_processados:
        nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes = dado
        time.sleep(2)
        historico.append_row([nome_grupo, midia_tipo, mensagem, midia_link, data, visualizacoes])


# Rota para exibir os dados processados
@app.route('/dados')
async def dados():
    async with TelegramClient(StringSession(string), api_id, api_hash, timeout=5) as client:
        dados_processados = await processar_grupos(client)
        return await render_template('telegram.html', dados=dados_processados)

# Rota para exibir os dados processados
@app.route('/planilha')
async def planilha():
    async with TelegramClient(StringSession(string), api_id, api_hash, timeout=5) as client:
        dados_processados = await processar_grupos(client)
        await enviar_para_planilha(dados_processados)
        return 'Os dados foram enviados para a planilha'
        

# Função para mensagens mais vistas
async def top_messages(client):
    mais_vistas_grupos = []

    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        time.sleep(2)
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=10,
            offset_date=seis_horas,
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
        top_5 = mais_vistas_grupos[:5]
        print(top_5)

    return mais_vistas_grupos


# Rota para visualizar as mensagens mais vistas
@app.route('/maisvistas')
async def mais_vistas():
    async with TelegramClient(StringSession(string), api_id, api_hash, timeout=5) as client:
        mais_vistas_grupos = await top_messages(client)
        return await render_template('maisvistas.html', mais_vistas=mais_vistas_grupos)

if __name__ == '__main__':
    app.run()




