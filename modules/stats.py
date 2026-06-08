# DESCRIÇÃO: Gestão de estatísticas, lucros acumulados e relatórios mensais.

import json
import os
from datetime import datetime

ARQUIVO_STATS = "stats_contas.json"

def carregar_stats():
    """Carrega o arquivo de estatísticas. Retorna um dicionário vazio se não existir."""
    if os.path.exists(ARQUIVO_STATS):
        try:
            with open(ARQUIVO_STATS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Arquivo de stats corrompido. Criando um novo.")
            return {}
    return {}

def salvar_stats(dados):
    """Salva o dicionário de estatísticas no arquivo JSON."""
    with open(ARQUIVO_STATS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def registrar_lucro_sessao(conta_nome, saldo_atual, lucro_da_sessao):
    """
    Atualiza o saldo atual e soma o lucro da sessão aos acumulados (Diário, Semanal e Mensal).
    Se o período virou, ele zera o respectivo acumulado automaticamente.
    """
    dados = carregar_stats()
    hoje = datetime.now()
    
    dia_atual = hoje.strftime("%Y-%m-%d")
    semana_atual = f"{hoje.year}-W{hoje.isocalendar()[1]}"
    mes_atual = hoje.strftime("%Y-%m")
    
    # Se a conta não existe ainda no JSON, cria a estrutura completa
    if conta_nome not in dados:
        dados[conta_nome] = {
            "saldo_atual": 0.0,
            "lucro_diario": 0.0,
            "lucro_semanal": 0.0,
            "lucro_mensal": 0.0,
            "dia_referencia": dia_atual,
            "semana_referencia": semana_atual,
            "mes_referencia": mes_atual
        }
        
    conta_stats = dados[conta_nome]
    
    # Verifica se virou o DIA
    if conta_stats.get("dia_referencia") != dia_atual:
        conta_stats["lucro_diario"] = 0.0
        conta_stats["dia_referencia"] = dia_atual
        
    # Verifica se virou a SEMANA
    if conta_stats.get("semana_referencia") != semana_atual:
        conta_stats["lucro_semanal"] = 0.0
        conta_stats["semana_referencia"] = semana_atual
        
    # Verifica se virou o MÊS
    if conta_stats.get("mes_referencia") != mes_atual:
        conta_stats["lucro_mensal"] = 0.0
        conta_stats["mes_referencia"] = mes_atual
        
    # Atualiza os valores somando o lucro da sessão atual
    conta_stats["saldo_atual"] = round(float(saldo_atual), 2)
    conta_stats["lucro_diario"] = round(conta_stats["lucro_diario"] + float(lucro_da_sessao), 2)
    conta_stats["lucro_semanal"] = round(conta_stats["lucro_semanal"] + float(lucro_da_sessao), 2)
    conta_stats["lucro_mensal"] = round(conta_stats["lucro_mensal"] + float(lucro_da_sessao), 2)
    
    # Salva de volta no arquivo
    salvar_stats(dados)
    print(f"📊 Stats {conta_nome}: Saldo ${conta_stats['saldo_atual']} | Lucro Dia: ${conta_stats['lucro_diario']} | Mês: ${conta_stats['lucro_mensal']}")

def gerar_relatorio_individual(conta_nome):
    """
    Gera um mini-relatório de uma conta específica (opcional, para uso interno do bot).
    """
    dados = carregar_stats()
    
    if conta_nome not in dados:
        return f"❌ Sem dados registrados para a conta {conta_nome} ainda."
        
    conta = dados[conta_nome]
    
    relatorio = (
        f"👤 *Conta:* `{conta_nome}`\n"
        f"💰 *Saldo Atual:* ${conta['saldo_atual']:.2f}\n"
        f"📈 *Lucro Hoje:* ${conta['lucro_diario']:.2f}\n"
        f"📅 *Lucro Mês:* ${conta['lucro_mensal']:.2f}"
    )
    return relatorio
