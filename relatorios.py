# DESCRIÇÃO: Gera e envia relatórios unificados (Diário, Semanal, Mensal) da banca.

import sys
import os
import urllib.request
import urllib.parse
from datetime import date, timedelta

# Importamos a função de leitura do nosso novo módulo de stats
from modules.stats import carregar_stats

# --- CONFIGURAÇÕES DO TELEGRAM ---
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

LIMITE_ALERTA_FALENCIA = 0.50  # Avisa se saldo < $0.50

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        urllib.request.urlopen(req)
        print("Resumo enviado ao Telegram com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def gerar_relatorio_agregado(tipo_relatorio):
    """
    Gera o relatório lendo diretamente os dados acumulados no stats_contas.json
    tipo_relatorio: 'diario', 'semanal' ou 'mensal'
    """
    dados = carregar_stats()
    
    if not dados:
        return "❌ Nenhum dado de estatística encontrado. Rode o bot primeiro para gerar saldo!"
        
    if tipo_relatorio == "diario":
        chave_lucro = "lucro_diario"
        titulo = "Diário"
    elif tipo_relatorio == "semanal":
        chave_lucro = "lucro_semanal"
        titulo = "Semanal"
    elif tipo_relatorio == "mensal":
        chave_lucro = "lucro_mensal"
        titulo = "Mensal"
    else:
        return "Tipo de relatório inválido."

    hoje = str(date.today())
    msg = f"📊 *Resumo {titulo} da Banca* ({hoje})\n\n"
    
    lucro_geral = 0.0
    contas_ativas = 0
    alerta_falencia = []
    
    for conta, info in dados.items():
        lucro = info.get(chave_lucro, 0.0)
        saldo = info.get("saldo_atual", 0.0)
        
        lucro_geral += lucro
        contas_ativas += 1
        
        icone = "🟢" if lucro > 0 else ("🔴" if lucro < 0 else "⚪")
        msg += f"{icone} *{conta}*: Lucro: `${lucro:.2f}` | Saldo Atual: `${saldo:.2f}`\n"
        
        if saldo < LIMITE_ALERTA_FALENCIA:
            alerta_falencia.append(f"⚠️ *{conta}* (Saldo: `${saldo:.2f}`)")

    msg += f"\n💰 *LUCRO TOTAL ({titulo.upper()}):* `${lucro_geral:.2f}`\n"
    msg += f"📈 Contas Operadas: {contas_ativas}\n"
    
    if alerta_falencia:
        msg += "\n🚨 *ALERTA DE RISCO DE FALÊNCIA* 🚨\n"
        msg += "\n".join(alerta_falencia)
        
    return msg

# --- FUNÇÕES DE CALENDÁRIO ---
def is_fim_de_semana(data_atual):
    """Retorna True se o dia atual for Domingo (0 = Segunda, 6 = Domingo)."""
    return data_atual.weekday() == 6

def is_ultimo_dia_do_mes(data_atual):
    """Retorna True se amanhã for um mês diferente de hoje."""
    amanha = data_atual + timedelta(days=1)
    return amanha.month != data_atual.month

if __name__ == "__main__":
    tipo = sys.argv[1].lower() if len(sys.argv) > 1 else "auto"
    hoje = date.today()
    
    if tipo == "auto":
        print("🤖 MODO AUTO: Verificando quais relatórios gerar hoje...")
        
        # 1. Sempre gera o diário
        print("Gerando relatório Diário...")
        msg_diaria = gerar_relatorio_agregado("diario")
        enviar_telegram(msg_diaria)
        
        # 2. Verifica se é fim de semana (Domingo)
        if is_fim_de_semana(hoje):
            print("📅 Hoje é Domingo! Gerando relatório Semanal...")
            msg_semanal = gerar_relatorio_agregado("semanal")
            enviar_telegram(msg_semanal)
            
        # 3. Verifica se é o último dia do mês
        if is_ultimo_dia_do_mes(hoje):
            print("🗓️ Hoje é o último dia do mês! Gerando relatório Mensal...")
            msg_mensal = gerar_relatorio_agregado("mensal")
            enviar_telegram(msg_mensal)
            
    elif tipo == "semanal":
        msg = gerar_relatorio_agregado("semanal")
        print(msg)
        enviar_telegram(msg)
    elif tipo == "mensal":
        msg = gerar_relatorio_agregado("mensal")
        print(msg)
        enviar_telegram(msg)
    else:
        msg = gerar_relatorio_agregado("diario")
        print(msg)
        enviar_telegram(msg)
