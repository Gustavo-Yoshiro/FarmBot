# DESCRIÇÃO: Funções para envio de mensagens via Telegram API.

import requests
from modules.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def enviar_mensagem_telegram(mensagem, conta_nome):
    """
    Envia uma mensagem para um chat específico no Telegram, incluindo o nome da conta.
    """
    mensagem_formatada = f"🤖 **Conta: {conta_nome}**\n\n{mensagem}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem_formatada,
        "parse_mode": "Markdown"
    }
    
    try:
        # Timeout de 20s para lidar com internet lenta
        response = requests.post(url, data=payload, timeout=20) 
        if response.status_code == 200:
            print(f"Notificação para '{conta_nome}' enviada com sucesso!")
        else:
            print(f"Falha ao enviar notificação: {response.text}")
    except Exception as e:
        print(f"Erro de conexão ao tentar enviar notificação: {e}")
