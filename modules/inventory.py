# ==============================================================================
# ARQUIVO: modules/inventory.py
# DESCRIÇÃO: Lógica para calcular a banca e vender itens do inventário.
# ==============================================================================
import time
import re
import random
from modules.config import *
import modules.state as state
from modules.navigation import clique_blindado, gerir_popups

def calcular_valor_total_conta(pagina, conta_nome, e_final=False, pode_falhar=False):
    """
    Navega até ao inventário, soma o saldo e o valor do botão 'Sell All'.
    """
    print("A calcular o valor total da conta (Saldo + Inventário)...")
    valor_inventario_centimos = 0
    saldo_atual_centimos = 0
    
    # Leitura inicial do saldo
    try:
        texto_dinheiro = pagina.locator(XPATH_DINHEIRO).inner_text()
        valor_em_string = re.sub(r'[^\d.]', '', texto_dinheiro)
        saldo_atual_centimos = int(float(valor_em_string) * 100) if valor_em_string else 0
        print(f"Saldo em caixa atual: ${saldo_atual_centimos / 100:.2f}")
    except Exception as e:
        print(f"Erro ao ler saldo inicial: {e}")
        saldo_atual_centimos = 0

    valor_encontrado = False 
    resultado_final = None

    try:
        for tentativa in range(3):
            if not state.executando and not e_final: 
                resultado_final = None
                break
            if state.bot_exit_code == 2: 
                resultado_final = None
                break

            print(f"--- Tentativa {tentativa + 1} de 3 para ler o saldo do inventário ---")
            
            # TENTATIVA 1: LÓGICA DE VENDA DE 1 ITEM + REFRESH
            if tentativa == 1: 
                print("Tentativa 1 falhou. Estratégia: Vender 1 item (Filtro Active) e Recarregar...")
                try:
                    gerir_popups(pagina)
                    if not state.executando and not e_final: break

                    menu_aberto_ou_perfil_visivel = pagina.locator(XPATH_BOTAO_PERFIL).is_visible()
                    
                    if not menu_aberto_ou_perfil_visivel:
                        if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu"):
                            print("Menu falhou. Tentando recarregar antes de continuar...")
                            pagina.reload(wait_until='domcontentloaded', timeout=15000)
                            time.sleep(3)
                            clique_blindado(pagina, XPATH_3_PONTOS, "Menu (Retry pós-reload)")
                        
                        time.sleep(2.0) 
                    else:
                        print("Botão de perfil já visível. Pulando clique no Menu.")

                    if not clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Botão Perfil"):
                        print("Botão Perfil falhou. Pulando estratégia de venda unitária.")
                        continue
                    
                    try:
                        if pagina.locator(SELETOR_FILTRO_ACTIVE).is_visible(timeout=5000):
                            clique_blindado(pagina, SELETOR_FILTRO_ACTIVE, "Filtro Active")
                            time.sleep(1.5)
                    except: pass

                    try:
                        pagina.wait_for_selector(SELETOR_DA_SKIN_PARA_VENDER, state='visible', timeout=5000)
                        itens_visiveis = pagina.locator(SELETOR_DA_SKIN_PARA_VENDER).all()
                        
                        if itens_visiveis:
                            for item in itens_visiveis:
                                if not state.executando and not e_final: break
                                try:
                                    item.scroll_into_view_if_needed()
                                    item.hover()
                                    time.sleep(1.0)
                                    botao_venda = item.locator(SELETOR_BOTAO_VENDA)
                                    if botao_venda.is_visible(timeout=1500):
                                        print("Item para desbugar encontrado. Vendendo...")
                                        botao_venda.click(force=True)
                                        pagina.wait_for_selector(SELETOR_BOTAO_CONFIRMAR_VENDA, timeout=5000)
                                        pagina.locator(SELETOR_BOTAO_CONFIRMAR_VENDA).click(force=True)
                                        time.sleep(3)
                                        break
                                except: continue
                    except: pass

                    print("Recarregando página (F5)...")
                    pagina.reload(wait_until='domcontentloaded', timeout=20000)
                    time.sleep(5) 
                    gerir_popups(pagina)
                    
                    try:
                        pagina.wait_for_selector(XPATH_DINHEIRO, timeout=10000)
                        txt = pagina.locator(XPATH_DINHEIRO).inner_text()
                        val = re.sub(r'[^\d.]', '', txt)
                        saldo_atual_centimos = int(float(val) * 100) if val else 0
                    except: pass

                except Exception: pass

            elif tentativa == 2: 
                print("Tentativa 2 falhou. Navegando via URL...")
                try:
                    pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=30000)
                    time.sleep(5) 
                    gerir_popups(pagina)
                except: pass
            
            if not state.executando and not e_final: 
                resultado_final = None
                break

            try:
                if not pagina.locator(SELETOR_BOTAO_SELL_ALL).is_visible(timeout=5000):
                    print("Navegando para o perfil...")
                    gerir_popups(pagina)
                    
                    if not pagina.locator(XPATH_BOTAO_PERFIL).is_visible():
                        if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu"):
                            print("Menu inacessível. Tentando ir para Home e tentar de novo...")
                            pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=20000)
                            time.sleep(4)
                            gerir_popups(pagina)
                            if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu (Retry URL)"):
                                continue 
                        
                        time.sleep(2.0) 

                    if not clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Perfil"): continue
                    pagina.wait_for_selector(SELETOR_BOTAO_SELL_ALL, state='attached', timeout=15000)

                botao_sell_all = pagina.locator(SELETOR_BOTAO_SELL_ALL)
                botao_sell_all.scroll_into_view_if_needed(timeout=5000)
                
                print("A aguardar o cálculo do preço do inventário (max 10s)...")
                
                regex_do_preco = re.compile(r'\(\s*\$\s*(\d+\.\d{2})\s*\)')
                start_time = time.time()
                
                while time.time() - start_time < 10: 
                    if not state.executando and not e_final: 
                        resultado_final = None
                        break 
                    try:
                        texto_botao = botao_sell_all.text_content() 
                        match = re.search(regex_do_preco, texto_botao)
                        if match:
                            print("Valor do inventário carregado.")
                            valor_inventario_string = match.group(1) 
                            valor_inventario_centimos = int(float(valor_inventario_string) * 100)
                            print(f"Inventário: ${valor_inventario_centimos / 100:.2f}")
                            valor_encontrado = True
                            break 
                    except: pass 
                    if valor_encontrado: break
                    time.sleep(0.5) 

                if valor_encontrado: break 
                
            except Exception as e_tentativa:
                print(f"Erro na tentativa {tentativa + 1}: {e_tentativa}")
        
        if valor_encontrado:
            total_centimos = saldo_atual_centimos + valor_inventario_centimos
            print(f"Valor Total da Conta: ${total_centimos / 100:.2f}")
            resultado_final = total_centimos
        elif e_final:
             print("A reportar N/D.")
             resultado_final = 0 
        elif pode_falhar:
            print("Aviso: Leitura falhou. Continuando...")
            resultado_final = None
        else:
            raise Exception("Falha crítica: Não foi possível ler o saldo inicial.")

    except Exception as e:
        print(f"Erro ao calcular: {e}")
        if "Falha crítica" in str(e): raise e
        if pode_falhar: resultado_final = None
        else: raise e
        
    finally:
        print("A retornar para a página principal...")
        if state.executando or e_final:
            clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Botão Voltar")
            try: 
                pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible', timeout=10000)
            except: 
                pass
        
    return resultado_final

def vender_itens_continuamente(pagina, meta_dinheiro, conta_nome, e_rotina_final=False):
    """
    Entra no modo de venda e vende itens até atingir a meta.
    BLINDADA CONTRA FALSA FALÊNCIA E VENDA INFINITA.
    """
    if not e_rotina_final:
        print("A iniciar processo de venda contínua...")
    
    gerir_popups(pagina)
    if not state.executando: return False

    clique_blindado(pagina, XPATH_3_PONTOS, "Menu")
    time.sleep(random.uniform(0.8, 1.3))
    clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Perfil")
    
    if not state.executando: return False

    # 1. Tentar carregar perfil (All)
    try:
        pagina.wait_for_selector(SELETOR_FILTRO_ALL, state='visible', timeout=15000)
        print("Perfil carregado.")
        
        try:
            print("Selecionando filtro 'All' para garantir itens vendáveis...")
            pagina.locator(SELETOR_FILTRO_ALL).click()
            time.sleep(2) 
        except Exception as e:
            print(f"Erro ao clicar no filtro All: {e}")

    except:
        print("Perfil não carregou a tempo na venda.")
        try: 
            pagina.reload(wait_until='domcontentloaded', timeout=15000)
            time.sleep(5) 
            gerir_popups(pagina)
            
            try:
                pagina.wait_for_selector(SELETOR_FILTRO_ALL, state='visible', timeout=10000)
                pagina.locator(SELETOR_FILTRO_ALL).click()
                time.sleep(2)
            except: pass
            
        except: return False
    
    # 2. Tentar carregar lista de itens (COM RETENTATIVA)
    items_loaded = False
    
    for i in range(2):
        if not state.executando: break
        print(f"Aguardando lista de itens (Tentativa {i+1})...")
        try:
            pagina.wait_for_selector(SELETOR_DA_SKIN_PARA_VENDER, state='visible', timeout=10000)
            items_loaded = True
            break
        except:
            print("Itens não apareceram. Clicando no filtro 'All' para forçar...")
            
            try:
                pagina.locator(SELETOR_FILTRO_ALL).click(force=True)
                time.sleep(3)
            except: pass
            
            if i == 0: 
                 print("Tentando filtro 'Active' para destravar lista...")
                 try: 
                     pagina.locator(SELETOR_FILTRO_ACTIVE).click()
                     time.sleep(2)
                     pagina.locator(SELETOR_FILTRO_ALL).click()
                     time.sleep(2)
                 except: pass

    if not items_loaded:
        print("⚠️ Atenção: Skins não detectadas após tentativas.")

    items_found = True
    vendas_realizadas = 0

    while state.executando:
        # FAILSAFE CRÍTICO
        if vendas_realizadas >= 6:
            print("🛑 LIMITE DE SEGURANÇA ATINGIDO (6 itens vendidos seguidos).")
            print("Parando venda forçadamente para forçar reavaliação geral do saldo na Home.")
            break

        try:
            texto_dinheiro = pagina.locator(XPATH_DINHEIRO).inner_text()
            valor_em_string = re.sub(r'[^\d.]', '', texto_dinheiro)
            dinheiro_atual = int(float(valor_em_string) * 100) if valor_em_string else 0
            
            print(f"[{vendas_realizadas} vendas feitas] Saldo visual: ${dinheiro_atual/100:.2f} | Meta: ${meta_dinheiro/100:.2f}")

            if dinheiro_atual >= meta_dinheiro:
                print("✅ Meta de dinheiro atingida!")
                items_found = True
                break

            itens_visiveis = pagina.locator(SELETOR_DA_SKIN_PARA_VENDER).all()
            
            if not itens_visiveis:
                print("Lista vazia. Tentando filtro 'Active' uma última vez...")
                try:
                    pagina.locator(SELETOR_FILTRO_ACTIVE).click()
                    time.sleep(2)
                    itens_visiveis = pagina.locator(SELETOR_DA_SKIN_PARA_VENDER).all()
                except: pass
                
                if not itens_visiveis:
                    print("Definitivamente nenhum item ativo encontrado para vender.")
                    items_found = False 
                    break

            venda_sucedida = False
            for item in itens_visiveis:
                if not state.executando: break
                
                try:
                    item.scroll_into_view_if_needed()
                    item.hover()
                    time.sleep(random.uniform(1.2, 2.0))
                    
                    botao_venda = item.locator(SELETOR_BOTAO_VENDA)
                    
                    if botao_venda.is_visible(timeout=1000):
                        print("Item vendável encontrado. A tentar vender...")
                        botao_venda.click(force=True)
                        
                        print("A aguardar e a confirmar a venda...")
                        pagina.locator(SELETOR_BOTAO_CONFIRMAR_VENDA).click(force=True, timeout=10000)
                        time.sleep(random.uniform(1.2, 2.0))
                        print("✅ Item vendido com sucesso!")
                        venda_sucedida = True
                        vendas_realizadas += 1
                        time.sleep(random.uniform(3, 5))
                        break
                    else:
                        print("Este item não é vendável. A procurar o próximo...")
                except Exception as e_item:
                    print(f"Aviso: Item ficou inacessível no DOM. Tentando próximo... ({e_item})")
                    continue
            
            if not venda_sucedida:
                print("Nenhum item vendável encontrado nesta página.")
                items_found = False
                break

        except Exception as e:
            print(f"Erro ao tentar vender um item: {e}")
            break

    print("A retornar para a tela principal...")
    clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Botão Voltar")
    try:
        pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible')
    except: pass
    
    return items_found
