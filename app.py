from quart import Quart, render_template
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from telethon.sessions import StringSession
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from scraping import processar_grupos, processar_grupos_doze, enviar_para_planilha, top_messages
app = Quart(__name__)


@app.route('/')
async def home():
    return await render_template('index.html')

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

# Credenciais Google Sheets
arquivo_credenciais ="projeto-final-insper-e3a4847fd379.json"
conteudo_credenciais = os.environ['key']
with open(arquivo_credenciais, mode="w") as arquivo:
    arquivo.write(conteudo_credenciais)
conta = ServiceAccountCredentials.from_json_keyfile_name(arquivo_credenciais)

api = gspread.authorize(conta)
planilha = api.open_by_key("1drW5e4xS54XvuULlR3hLdgQRdSahB4-VJKnq8rb4fJI")
historico = planilha.worksheet("Historico")


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
        dados_processados_doze = await processar_grupos_doze(client)
        await enviar_para_planilha(dados_processados_doze)
        return 'Os dados foram enviados para a planilha'
    
# Rota para visualizar as mensagens mais vistas
@app.route('/maisvistas')
async def mais_vistas():
    async with TelegramClient(StringSession(string), api_id, api_hash, timeout=5) as client:
        top_mensagens = await top_messages(client)
        return await render_template('maisvistas.html', top_mensagens=top_mensagens)

if __name__ == '__main__':
    app.run()




