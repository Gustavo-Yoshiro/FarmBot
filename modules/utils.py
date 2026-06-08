# DESCRIÇÃO: Funções auxiliares de sistema, arquivos e sinais.

import os
import time
import modules.state as state
import json
from datetime import date
from modules.telegram import enviar_mensagem_telegram

def obter_saldo_inicial_persistente(conta_nome, saldo_atual_lido):
    """
    Tenta ler o saldo inicial de um arquivo.
    Se não existir, cria o arquivo com o saldo atual (início do dia).
    """
    arquivo_saldo = f"saldo_inicial_{conta_nome}.txt"
    
    if os.path.exists(arquivo_saldo):
        try:
            with open(arquivo_saldo, "r") as f:
                saldo_salvo = float(f.read().strip())
            print(f"🔄 Histórico encontrado! Saldo Inicial do Dia: ${saldo_salvo/100:.2f}")
            return int(saldo_salvo) # Retorna em centavos
        except Exception as e:
            print(f"Erro ao ler arquivo de saldo: {e}. Usando saldo atual como novo inicial.")
    
    with open(arquivo_saldo, "w") as f:
        f.write(str(saldo_atual_lido))
    print(f"🆕 Novo dia/sessão: Saldo inicial registrado (${saldo_atual_lido/100:.2f})")
    return saldo_atual_lido

def criar_signal_handler(conta_nome):
    """Cria o handler para capturar o Ctrl+C e parar o bot suavemente."""
    def signal_handler(sig, frame):
        print(f"\n!!! Ctrl+C pressionado para a conta '{conta_nome}'. A encerrar... !!!")
        enviar_mensagem_telegram(f"🛑 *Parado manualmente pelo utilizador.*", conta_nome)
        state.executando = False
        state.bot_exit_code = 2 
    return signal_handler

def dormir_com_verificacao(segundos):
    """
    Dorme pela quantidade de segundos, mas verifica a cada 0.1s 
    se o bot foi desligado. Permite resposta rápida ao Ctrl+C.
    """
    passos = int(segundos * 10)
    for _ in range(passos):
        if not state.executando:
            return
        time.sleep(0.1)
        
def salvar_dados_relatorio(conta_nome, saldo_centavos, lucro_centavos):
    """Salva o saldo e o lucro diário da conta em um banco JSON."""
    arquivo = "historico_banca.json"
    hoje = str(date.today())
    
    dados = {}
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
        except json.JSONDecodeError:
            pass
            
    if conta_nome not in dados:
        dados[conta_nome] = {"saldo_atual": 0.0, "historico": {}}
        
    saldo_dolar = saldo_centavos / 100.0 if saldo_centavos is not None else 0.0
    lucro_dolar = lucro_centavos / 100.0 if lucro_centavos is not None else 0.0
    
    dados[conta_nome]["saldo_atual"] = saldo_dolar
    dados[conta_nome]["historico"][hoje] = {
        "lucro": lucro_dolar,
        "saldo": saldo_dolar
    }
    
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4)
