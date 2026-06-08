# DESCRIÇÃO: Lógica para missões diárias e recolha de cristais/caixas bônus.

import time
import re
import random
import os
from modules.config import *
import modules.state as state
from modules.navigation import clique_blindado, gerir_popups
from modules.game_utils import ler_quantidade_cristais, aplicar_estrategia_recuperacao

def sincronizar_vitorias(pagina):
    """Navega até às recompensas diárias, lê o progresso da missão e retorna o número de vitórias."""
    print("Sincronizando contador de vitórias com o site...")
    vitorias_atuais = -1
    try:
        if not state.executando: return -1
        gerir_popups(pagina)
        
        if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu (3 Pontos)"): return -1
        time.sleep(random.uniform(0.5, 1.0)) 
        
        if not state.executando: return -1
        
        if not clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Botão Perfil"): return -1
        
        try:
            pagina.wait_for_selector(SELETOR_RECOMPENSAS_DIARIAS, state='visible', timeout=15000)
            pagina.locator(SELETOR_RECOMPENSAS_DIARIAS).click()
            
            missao = pagina.locator(SELETOR_TEXTO_MISSAO)
            missao.scroll_into_view_if_needed()
            
            texto_da_missao = missao.inner_text()
            
            match = re.search(r'\((\d)/3\)', texto_da_missao)
            if match:
                vitorias_atuais = int(match.group(1))
                print(f"Estado da missão no site: ({vitorias_atuais}/3). Contador sincronizado.")
            else:
                print("Não foi possível encontrar o padrão de progresso (X/3) na missão.")
        except:
            print("Erro ao ler missão (timeout visual).")

    except Exception as e:
        print(f"Erro ao sincronizar vitórias: {e}. A manter o contador atual.")
    finally:
        print("A retornar para a página principal...")
        if state.executando:
            clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Botão Voltar")
            try:
                pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible', timeout=10000)
            except:
                pass

def recolher_recompensas(pagina, conta_nome, verificacao_dura=True):
    """
    Navega até às recompensas diárias, recolhe missões e tenta abrir a caixa bônus.
    O parâmetro 'verificacao_dura' força a cobrança de 98 cristais.
    """
    print("\n--- RECOLHENDO RECOMPENSAS DIÁRIAS ---")
    try:
        gerir_popups(pagina)
        
        # 1. Ler Cristais Iniciais
        cristais_iniciais = ler_quantidade_cristais(pagina)
        print(f"💎 Cristais Iniciais: {cristais_iniciais}")
        
        # Navegação
        print("Navegando para Daily Rewards...")
        if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu"): return
        time.sleep(1)
        if not clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Perfil"): return
        
        try:
            pagina.wait_for_selector(SELETOR_RECOMPENSAS_DIARIAS, state='visible', timeout=10000)
            pagina.locator(SELETOR_RECOMPENSAS_DIARIAS).click()
            pagina.wait_for_timeout(2500) 
        except Exception as e:
            print(f"Erro ao abrir aba de recompensas: {e}")
            return

        # 2. Recolher Recompensas
        print("Iniciando coleta sequencial...")
        for i in range(10):
            if not state.executando: break
            
            botoes_visiveis = pagina.locator(SELETOR_BOTAO_GET_REWARD).all()
            clicou_neste_ciclo = False
            
            for botao in botoes_visiveis:
                if not state.executando: break
                
                if botao.is_visible() and botao.is_enabled():
                    try:
                        botao.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        
                        texto_btn = botao.inner_text().lower()
                        if "done" in texto_btn or "collected" in texto_btn:
                            continue 

                        print(f"Clicando em recompensa (Iteração {i+1})...")
                        botao.click(force=True)
                        clicou_neste_ciclo = True
                        time.sleep(random.uniform(2.0, 3.0))
                        break 
                    except Exception as e:
                        print(f"Erro ao clicar: {e}")
            
            if not clicou_neste_ciclo:
                print("Todas as recompensas disponíveis foram recolhidas.")
                break

        # Atualiza cristais
        time.sleep(2)
        cristais_finais = ler_quantidade_cristais(pagina)
        cristais_ganhos = cristais_finais - cristais_iniciais
        print(f"💎 Cristais Finais: {cristais_finais} (Variação: +{cristais_ganhos})")

        # VERIFICAÇÃO DE SUCESSO (DURA OU SIMPLES)
        if verificacao_dura:
            if cristais_ganhos < 98 and state.executando:
                print(f"⚠️ VERIFICAÇÃO DURA: Apenas {cristais_ganhos} cristais recolhidos (Esperado: 98+).")
                print("Forçando recarregamento da página para tentar recolher o restante (1x)...")
                try:
                    pagina.reload(wait_until='domcontentloaded', timeout=30000)
                    time.sleep(5)
                    gerir_popups(pagina)
                    
                    clique_blindado(pagina, XPATH_3_PONTOS, "Menu")
                    time.sleep(1.5)
                    clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Perfil")
                    pagina.wait_for_selector(SELETOR_RECOMPENSAS_DIARIAS, state='visible', timeout=10000)
                    pagina.locator(SELETOR_RECOMPENSAS_DIARIAS).click()
                    pagina.wait_for_timeout(3000)
                    
                    for i in range(5):
                        if not state.executando: break
                        botoes_visiveis = pagina.locator(SELETOR_BOTAO_GET_REWARD).all()
                        clicou_neste_ciclo = False
                        for botao in botoes_visiveis:
                            if botao.is_visible() and botao.is_enabled():
                                texto_btn = botao.inner_text().lower()
                                if "done" not in texto_btn and "collected" not in texto_btn:
                                    botao.click(force=True)
                                    clicou_neste_ciclo = True
                                    time.sleep(random.uniform(2.0, 3.0))
                                    break
                        if not clicou_neste_ciclo:
                            break
                    
                    time.sleep(2)
                    cristais_finais = ler_quantidade_cristais(pagina)
                    cristais_ganhos = cristais_finais - cristais_iniciais
                    print(f"💎 Cristais Finais (Pós-revisão): {cristais_finais} (Variação Total: +{cristais_ganhos})")
                    
                    if cristais_ganhos < 98:
                        print("❌ ALERTA CRÍTICO: Recompensas incompletas mesmo após revisão! Pode ser erro no site ou missão não finalizada.")
                    else:
                        print("✅ Revisão de cristais bem-sucedida (98+).")
                        
                except Exception as e_rev:
                    print(f"Erro na revisão de cristais: {e_rev}")
        else:
            if cristais_ganhos > 0:
                print(f"✅ Recompensas parciais recolhidas com sucesso (+{cristais_ganhos} cristais).")
            else:
                print("ℹ️ Nenhuma recompensa parcial disponível para recolher neste momento.")

        cristais_reserva = 0
        if os.path.exists("cristais_reserva.txt"):
            try:
                with open("cristais_reserva.txt", "r") as f:
                    conteudo = f.read().strip()
                    if conteudo.isdigit():
                        cristais_reserva = int(conteudo)
                        print(f"📦 INFO: Ficheiro 'cristais_reserva.txt' lido. Guardando reserva de {cristais_reserva} cristais.")
            except Exception as e:
                print(f"Erro ao ler cristais_reserva.txt: {e}")

        # --- GRAN FINALE: ABRIR CAIXA BÔNUS (GLIMMER) ---
        seletor_local_glimmer = 'a.full-size[href="/crystal-glimmer"]'
        seletor_local_abrir = 'button.base-button.open-btn'

        if (cristais_finais - cristais_reserva) >= 100 and state.executando:
            print("Navegando para a página inicial para localizar a caixa Glimmer...")
            try:
                pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=30000)
                time.sleep(6) 
                gerir_popups(pagina) 
            except Exception as e_nav:
                print(f"Aviso: Erro ao ir para home: {e_nav}")

        tentativas_erro_glimmer = 0 
        glimmer_aberta = False #

        # LOOP LIMITADO A UMA ABERTURA DE CAIXA
        while (cristais_finais - cristais_reserva) >= 100 and state.executando and not glimmer_aberta:
            
            if tentativas_erro_glimmer > 10:
                print("🛑 Limite extremo de retentativas atingido (10x). Abortando Glimmer por segurança.")
                break

            print(f"\n✨ SALDO SUFICIENTE (Disponível: {cristais_finais} | Reserva: {cristais_reserva})! Tentando abrir UMA Caixa Bônus...")
            
            saldo_antes_clique = ler_quantidade_cristais(pagina)
            if (saldo_antes_clique - cristais_reserva) < 100:
                print("Saldo insuficiente (considerando reserva) detetado antes do clique. Abortando.")
                break

            try:
                caixa_encontrada = False
                caixa_locator = pagina.locator(seletor_local_glimmer).first

                for i in range(5):
                    if caixa_locator.is_visible():
                        caixa_encontrada = True
                        break
                    print(f"Procurando caixa Glimmer (Scroll {i+1}/5)...")
                    pagina.mouse.wheel(0, 1000) 
                    time.sleep(1.5)
                
                if caixa_encontrada:
                    print("Caixa Glimmer encontrada!")
                    caixa_locator.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    caixa_locator.click(force=True)
                    time.sleep(1.5)

                    botao_abrir = pagina.locator(seletor_local_abrir).first
                    try:
                        botao_abrir.wait_for(state='visible', timeout=10000)
                        
                        if not botao_abrir.is_enabled():
                            print("Botão 'Open' encontrado, mas está desabilitado.")
                            tentativas_erro_glimmer += 1
                            aplicar_estrategia_recuperacao(pagina, tentativas_erro_glimmer)
                            continue 

                        botao_abrir.click(force=True)
                        print("Botão 'Open' clicado. Verificando...")
                        time.sleep(2)

                        try:
                            erro_visual = pagina.locator('text=/server error|error occurred|try again/i').first
                            if erro_visual.is_visible(timeout=3000):
                                print(f"❌ Erro visual detectado: '{erro_visual.inner_text()}'.")
                        except:
                            time.sleep(5) 
                        
                        print("Recarregando página (F5) para confirmar abertura...")
                        pagina.reload(wait_until='domcontentloaded')
                        time.sleep(5)
                        gerir_popups(pagina) 
                        
                        novo_saldo = ler_quantidade_cristais(pagina)

                        if novo_saldo <= (saldo_antes_clique - 100):
                            print(f"✅ Sucesso! Caixa Glimmer aberta. ({saldo_antes_clique} -> {novo_saldo})")
                            cristais_finais = novo_saldo
                            tentativas_erro_glimmer = 0 
                            glimmer_aberta = True # MARCA COMO ABERTA E QUEBRA O LOOP
                            print("🎯 Limite de 1 caixa Glimmer atingido. Encerrando rotina de Glimmer.")
                            break
                        else:
                            print(f"⚠️ Saldo INALTERADO ({saldo_antes_clique}). Abertura falhou ou Server Error.")
                            tentativas_erro_glimmer += 1 
                            aplicar_estrategia_recuperacao(pagina, tentativas_erro_glimmer)
                            cristais_finais = ler_quantidade_cristais(pagina)
                            continue 

                    except Exception as e_btn:
                        print(f"Erro ao interagir com botão abrir: {e_btn}")
                        tentativas_erro_glimmer += 1
                        aplicar_estrategia_recuperacao(pagina, tentativas_erro_glimmer)
                        cristais_finais = ler_quantidade_cristais(pagina)
                        continue 
                else:
                    print("Caixa Glimmer não encontrada mesmo após scroll. Saindo da rotina Glimmer.")
                    break 

            except Exception as e_bonus:
                print(f"Erro na caixa bônus: {e_bonus}")
                tentativas_erro_glimmer += 1
                aplicar_estrategia_recuperacao(pagina, tentativas_erro_glimmer)
                continue 
        
        if not glimmer_aberta and (cristais_finais - cristais_reserva) < 100:
            print(f"Saldo disponível para caixas esgotado ou bloqueado pela reserva. (Cristais: {cristais_finais} | Reserva: {cristais_reserva})")

    except Exception as e:
        print(f"Erro geral ao recolher recompensas: {e}")
    finally:
        print("Retornando para a tela principal...")
        clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Botão Voltar")
        try:
            pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible', timeout=10000)
        except:
            pass
