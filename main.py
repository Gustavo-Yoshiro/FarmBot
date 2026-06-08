# DESCRIÇÃO: Ponto de entrada principal do bot (Com Relatórios e Segurança).

import sys
import time
import random
import os
import signal 
import re  
from playwright.sync_api import sync_playwright

# Importação dos módulos de estado e configuração
import modules.state as state
from modules.config import *
from modules.telegram import enviar_mensagem_telegram

# Importação dos utilitários
from modules.utils import (
    obter_saldo_inicial_persistente, 
    criar_signal_handler,
    dormir_com_verificacao
)

from modules.stats import registrar_lucro_sessao

# Módulos de organização, setup e navegação
from modules.setup import inicializar_navegador, verificar_acesso_inicial
from modules.auth import tentar_login_automatico
from modules.navigation import recuperar_bot, gerir_popups, clique_blindado

# --- IMPORTAÇÕES MODULARIZADAS ---
from modules.rewards import sincronizar_vitorias, recolher_recompensas
from modules.inventory import calcular_valor_total_conta, vender_itens_continuamente
from modules.boxes import abrir_caixa_final
# ---------------------------------------

def rodar_bot(conta_nome, forcar_relogin=False):
    # Inicializa variáveis globais de estado
    state.executando = True
    state.bot_exit_code = 0
    signal.signal(signal.SIGINT, criar_signal_handler(conta_nome))
    
    ESTADO_DE_SESSAO = f"{conta_nome}.json"
    
    # Variáveis de controle do jogo
    concluido = False 
    batalhas_realizadas = 0
    vitorias_consecutivas_locais = 0 
    
    valor_inicial = 0
    ultima_batalha_sincronizada = 0
    ultima_batalha_stoploss = 0
    
    # Flags de estratégia e segurança
    saldo_inicial_pendente = False 
    verificacao_lucro_pendente = False 
    ignorar_stop_parcial = False 
    
    erros_consecutivos = 0 

    # Check rápido de arquivo antes de abrir navegador
    if not os.path.exists(ESTADO_DE_SESSAO) and not forcar_relogin:
        print(f"⚠️ Sessão '{ESTADO_DE_SESSAO}' não encontrada.")
        print("ℹ️ Encerrando para agendar relogin manual.")
        state.bot_exit_code = 3 
        return

    with sync_playwright() as p:
        # 1. Configuração do Navegador
        navegador, contexto, pagina = inicializar_navegador(p, conta_nome)
        
        # 2. Verificação de Acesso e Login
        acesso_liberado = verificar_acesso_inicial(pagina, contexto, conta_nome, forcar_relogin)
        
        if not acesso_liberado:
            navegador.close()
            return 

        # Limpeza de Pop-ups Inicial
        print("Aguardando carregamento completo da página inicial...")
        time.sleep(5) 
        gerir_popups(pagina)

        print(f"\n>>> Bot iniciado para a conta '{conta_nome}'! <<<")
        
        # 3. Leitura Inicial de Saldo
        saldo_atual_site_temp = calcular_valor_total_conta(pagina, conta_nome, e_final=False, pode_falhar=True)
        
        if saldo_atual_site_temp is not None:
            saldo_atual_site = saldo_atual_site_temp
            valor_inicial = obter_saldo_inicial_persistente(conta_nome, saldo_atual_site)
            
            print(f"Valor Inicial de Referência: ${valor_inicial / 100:.2f}")
            print(f"Saldo Atual no Site: ${saldo_atual_site / 100:.2f}")
            
            lucro_acumulado_inicio = saldo_atual_site - valor_inicial
            if lucro_acumulado_inicio <= LIMITE_PULA_CONTA:
                print(f"⚠️ Modo Recuperação Ativado: Prejuízo acumulado de ${lucro_acumulado_inicio/100:.2f}.")
                ignorar_stop_parcial = True
        else:
            print("⚠️ AVISO: Não foi possível ler o saldo inicial do inventário.")
            saldo_inicial_pendente = True
            valor_inicial = 0
            print("Bot iniciado com Saldo Pendente.")

        # 4. Loop Principal do Jogo
        while state.executando:
            try:
                gerir_popups(pagina)

                # Checagem de sessão no meio do loop
                try:
                    if pagina.locator(SELETOR_BOTAO_LOGIN).is_visible(timeout=5000):
                        print("!!! SESSÃO EXPIRADA DETECTADA !!!")
                        if tentar_login_automatico(pagina, contexto, ESTADO_DE_SESSAO):
                            print("✅ Sessão renovada com sucesso! Continuando...")
                        else:
                            enviar_mensagem_telegram("⌛️ *Sessão Expirada!* Auto-login falhou.", conta_nome)
                            state.bot_exit_code = 3 
                            break 
                except Exception:
                    pass
                
                status_missao = "CONCLUÍDA ✅" if concluido else f"PENDENTE ({vitorias_consecutivas_locais} wins seguidas)"
                print(f"\n--- Iniciando Ciclo (Batalhas: {batalhas_realizadas} | Missão: {status_missao}) ---")

                # (A) Tenta ler saldo pendente
                if saldo_inicial_pendente and not concluido:
                    print("Tentando ler saldo inicial pendente...")
                    saldo_temp = calcular_valor_total_conta(pagina, conta_nome, e_final=False, pode_falhar=True)
                    if saldo_temp is not None:
                        valor_inicial = obter_saldo_inicial_persistente(conta_nome, saldo_temp)
                        saldo_inicial_pendente = False
                        lucro_acumulado = saldo_temp - valor_inicial
                        if lucro_acumulado <= LIMITE_PULA_CONTA:
                            ignorar_stop_parcial = True
                            print(f"⚠️ Modo Recuperação Ativado (Tardio): Saldo recuperado: ${valor_inicial/100:.2f}")
                        else:
                            print(f"Saldo recuperado: ${valor_inicial/100:.2f}")

                if not state.executando: break

                # (B) Sincronização da Missão
                if not concluido:
                    check_seguranca = (batalhas_realizadas > 0 and 
                                       batalhas_realizadas % 3 == 0 and 
                                       batalhas_realizadas != ultima_batalha_sincronizada)
                    
                    check_vitoria = (vitorias_consecutivas_locais >= 3)

                    if check_seguranca or check_vitoria:
                        motivo = "3 Vitórias Seguidas!" if check_vitoria else "Checagem de Segurança (3 Batalhas)"
                        print(f"Sincronizando... Motivo: {motivo}")
                        
                        vitorias_site = sincronizar_vitorias(pagina)
                        
                        if vitorias_site != -1:
                            ultima_batalha_sincronizada = batalhas_realizadas
                            vitorias_consecutivas_locais = vitorias_site
                            
                            if vitorias_site >= 3:
                                concluido = True
                                print("!!! MISSÃO CONCLUÍDA !!!")
                                print("🚀 Entrando em modo FARM (Stop Loss e Sync desativados).")
                            else:
                                print(f"Missão ainda pendente ({vitorias_site}/3).")

                # (C) Verificação de Stop Loss
                if not concluido:
                    if (batalhas_realizadas > 0 and 
                        batalhas_realizadas % 4 == 0 and 
                        batalhas_realizadas != ultima_batalha_stoploss):
                        verificacao_lucro_pendente = True
                        ultima_batalha_stoploss = batalhas_realizadas

                    if verificacao_lucro_pendente and not saldo_inicial_pendente:
                        print("Verificando Stop Loss (Modo Segurança)...")
                        valor_atual_temp = calcular_valor_total_conta(pagina, conta_nome, e_final=False, pode_falhar=True)
                        
                        if valor_atual_temp is not None:
                            verificacao_lucro_pendente = False 
                            lucro_temp = valor_atual_temp - valor_inicial
                            
                            if lucro_temp <= LIMITE_PARA_CONTA: 
                                print(f"⚠️ Limite Total (Stop Loss): ${lucro_temp/100:.2f}")
                                state.bot_exit_code = 4 
                                print("🛡️ Recolhendo recompensas antes de encerrar por Stop Loss...")
                                recolher_recompensas(pagina, conta_nome, verificacao_dura=False)
                                break
                            elif lucro_temp <= LIMITE_PULA_CONTA: 
                                if ignorar_stop_parcial:
                                    print(f"📉 Prejuízo ignorado (Modo Recuperação Ativo).")
                                else:
                                    print(f"⚠️ Limite Parcial (Pula Conta): ${lucro_temp/100:.2f}")
                                    state.bot_exit_code = 5 
                                    break
                            else:
                                print(f"Lucro atual: ${lucro_temp/100:.2f}. OK.")

                if not state.executando: break

                # (D) Decisão de Jogo: Batalhar ou Vender
                dinheiro = 0
                leitura_valida = False
                
                # Leitura de saldo
                for tentativa_leitura in range(2): 
                    try:
                        for i in range(5):
                            try:
                                element_dinheiro = pagina.locator(XPATH_DINHEIRO)
                                if element_dinheiro.is_visible():
                                    txt = element_dinheiro.inner_text()
                                    val = re.sub(r'[^\d.]', '', txt)
                                    if val:
                                        dinheiro_lido = int(float(val) * 100)
                                        if dinheiro_lido > 0:
                                            dinheiro = dinheiro_lido
                                            leitura_valida = True
                                            break 
                                dinheiro = 0 
                            except: pass
                            time.sleep(1.0)
                        
                        if leitura_valida: break 
                        
                        if tentativa_leitura == 0 and dinheiro == 0:
                            print("⚠️ Saldo visual $0.00. Navegando para URL principal...")
                            try:
                                pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=30000)
                                time.sleep(6) 
                                gerir_popups(pagina)
                            except: pass
                            
                    except Exception as e:
                        print(f"Aviso leitura saldo: {e}")
                        pass
                
                print(f"Dinheiro: {dinheiro} | Custo: {CUSTO_DA_BATALHA}")

                if dinheiro >= CUSTO_DA_BATALHA:
                    # TENTA BATALHAR
                    try:
                        print("Batalhando...")
                        clique_blindado(pagina, SELETOR_TELA_DE_BATALHA, "Botão Farm Zone")
                        pagina.wait_for_selector(XPATH_CRIAR_BATALHA, state='visible')
                        
                        pagina.locator(XPATH_CRIAR_BATALHA).click()
                        pagina.locator(SELETOR_CAIXA_PARA_BATALHA).click()
                        dormir_com_verificacao(random.uniform(0.8, 1.3))
                        pagina.locator(XPATH_CONFIRMAR_BATALHA).click()
                        dormir_com_verificacao(random.uniform(0.9, 1.5))
                        pagina.locator(XPATH_BOTAO_INICIAR_BATALHA).click()

                        # Espera resultado
                        pagina.wait_for_selector(f"{SELETOR_VITORIA}, {SELETOR_DERROTA}", timeout=300000)
                        vitoria_nesta_ronda = pagina.locator(SELETOR_VITORIA).is_visible()
                        dormir_com_verificacao(random.uniform(1.5, 2.5))
                        pagina.locator(XPATH_X_FECHAR_RESULTADO).click()

                        batalhas_realizadas += 1 
                        erros_consecutivos = 0 

                        if vitoria_nesta_ronda:
                            print("Resultado: VITÓRIA 🟢")
                            vitorias_consecutivas_locais += 1 
                            if concluido: 
                                print("Farmando... (Meta já batida)")
                        else:
                            print("Resultado: DERROTA 🔴")
                            vitorias_consecutivas_locais = 0 
                            
                            if concluido:
                                print("Missão cumprida e derrota ocorrida. Hora da recompensa final!")
                                abrir_caixa_final(pagina, conta_nome)
                                break 

                    except Exception as e:
                        erros_consecutivos += 1
                        print(f"⚠️ Erro na batalha ({erros_consecutivos}/3): {e}")
                        
                        if erros_consecutivos >= 3:
                            print("❌ Falha crítica recorrente.")
                            state.bot_exit_code = 1 
                            break
                        if not recuperar_bot(pagina, URL_DO_JOGO, conta_nome): break
                        continue
                
                else: 
                    # Saldo insuficiente -> Vender
                    print(f"⚠️ Saldo baixo (${dinheiro/100:.2f}). Indo para vendas...")
                    tem_itens = vender_itens_continuamente(pagina, 2 * CUSTO_DA_BATALHA, conta_nome)
                    erros_consecutivos = 0 
                    
                    if not tem_itens:
                        print("Verificando saldo final...")
                        try:
                            pagina.wait_for_selector(XPATH_DINHEIRO, state="visible", timeout=5000)
                            txt = pagina.locator(XPATH_DINHEIRO).inner_text()
                            val = re.sub(r'[^\d.]', '', txt)
                            dinheiro_final_check = int(float(val) * 100) if val else 0
                        except: dinheiro_final_check = 0

                        if dinheiro_final_check >= CUSTO_DA_BATALHA:
                             print(f"😅 Saldo recuperado: ${dinheiro_final_check/100:.2f}.")
                             continue 

                        print("⚠️ BANCA QUEBRADA.")
                        enviar_mensagem_telegram(f"⛔ *FALÊNCIA:* Sem dinheiro/skins.", conta_nome)
                        state.bot_exit_code = 4
                        print("🛡️ Recolhendo recompensas antes de encerrar (Falência)...")
                        recolher_recompensas(pagina, conta_nome, verificacao_dura=False)
                        break

                if not state.executando: break
                
                if not pagina.locator(SELETOR_TELA_DE_BATALHA).is_visible(timeout=5000):
                    print("Voltando ao menu...")
                    clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Botão Voltar")
                    try: pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible', timeout=10000)
                    except: pass

                print(f"Ciclo concluído. Pausa...")
                dormir_com_verificacao(random.uniform(3, 6))

            except Exception as e:
                erros_consecutivos += 1
                print(f"!!! Erro inesperado ({erros_consecutivos}/3): {e}")
                if erros_consecutivos >= 3:
                    state.bot_exit_code = 1
                    break
                if not recuperar_bot(pagina, URL_DO_JOGO, conta_nome): break 
                continue
        
        # 5. Relatório Final
        lucro_formatado_para_bash = "N/D" 
        try:
            print("Calculando fechamento...")
            valor_final = calcular_valor_total_conta(pagina, conta_nome, e_final=True, pode_falhar=False)
            
            lucro_centavos = None
            if valor_final and not saldo_inicial_pendente:
                lucro_centavos = valor_final - valor_inicial
                lucro_formatado_para_bash = f"${lucro_centavos / 100:.2f}"
            else:
                lucro_formatado_para_bash = "N/D"
            
            print(f"LUCRO_FINAL:{lucro_formatado_para_bash}") 

            # SALVA OS DADOS PARA O RELATÓRIO GERAL (stats.py fará o acúmulo inteligente)
            if valor_final is not None:
                saldo_em_dolar = valor_final / 100.0
                lucro_em_dolar = (lucro_centavos / 100.0) if lucro_centavos is not None else 0.0
                registrar_lucro_sessao(conta_nome, saldo_em_dolar, lucro_em_dolar)

            print(f"Conta '{conta_nome}' finalizada com lucro de {lucro_formatado_para_bash}. Relatório salvo.")
        
        except Exception as e:
            print(f"LUCRO_FINAL:N/D") 

        if state.bot_exit_code != 0 and state.bot_exit_code != 3:
            contexto.storage_state(path=ESTADO_DE_SESSAO)
            
        time.sleep(2) 
        
    print(f"Programa finalizado.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: Forneça o nome da conta.")
        sys.exit(1) 
    
    nome_da_conta = sys.argv[1]
    modo_relogin = False
    if len(sys.argv) > 2 and sys.argv[2] == "relogin":
        modo_relogin = True
        
    rodar_bot(nome_da_conta, forcar_relogin=modo_relogin)
    sys.exit(state.bot_exit_code)
