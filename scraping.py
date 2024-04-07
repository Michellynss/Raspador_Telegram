from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import time
from telethon.tl.types import InputPeerChannel, MessageMediaPhoto, MessageMediaDocument
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import asyncio

# Credenciais do Telegram
api_id = os.environ['id']
api_hash = os.environ['hash']
telefone = os.environ['fone']
string = os.environ['string']

async def conecta():
    client = TelegramClient(StringSession(string), api_id, api_hash)
    await client.start(telefone)
    await client.connect()
    return client

# Credenciais do Google Sheets
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

# Função que processa as mensagens das últimas seis horas
async def processar_grupos(client):
    dados_processados = []
    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        await asyncio.sleep(2)
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=50,
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

# Função que processa as mensagens das últimas doze horas
async def processar_grupos_doze(client):
    dados_processados_doze = []
    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        await asyncio.sleep(2)
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=50,
            offset_date=doze_horas,
            reverse=True)

        for message in messages:
            nome_grupo = obter_grupo(group_entity)
            mensagem = obter_mensagem(message)
            midia_tipo = tipo_midia(message)
            midia_link = obter_link(message)
            data =  obter_data(message)
            visualizacoes = obter_visualizacoes(message)         
            dados_processados_doze.append((nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes))
 
    return dados_processados_doze

async def enviar_para_planilha(dados_processados_doze):
    for dado in dados_processados_doze:
        nome_grupo, mensagem, midia_tipo, midia_link, data, visualizacoes = dado
        time.sleep(2)
        historico.append_row([nome_grupo, midia_tipo, mensagem, midia_link, data, visualizacoes])

# Função que processa as mensagens mais vistas das últimas seis horas
async def top_messages(client):

    mais_vistas_grupos = []

    for grupo in grupos:
        group_entity = await client.get_entity(grupo)
        group_input_peer = InputPeerChannel(group_entity.id, group_entity.access_hash)
        await time.sleep(2)  
        messages = await client.get_messages(
            entity=group_input_peer,
            limit=50,
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
    top_mensagens = mais_vistas_grupos[:20] 
    return top_mensagens
