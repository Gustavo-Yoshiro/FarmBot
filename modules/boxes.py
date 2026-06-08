# DESCRIÇÃO: Lógica para abrir a caixa Mil-Spec no final do ciclo (Modo Silencioso).

import time
import random
import re
from modules.config import *
import modules.state as state
from modules.telegram import enviar_mensagem_telegram
from modules.navigation import clique_blindado, gerir_popups, recuperar_bot
from modules.game_utils import aplicar_estrategia_recuperacao
from modules.inventory import vender_itens_continuamente
from modules.rewards import recolher_recompensas

def abrir_caixa_final(pagina, conta_nome):
    """Rotina final para abrir a caixa 'Mil-Spec' antes de encerrar."""
    print("\n--- INICIANDO ROTINA FINAL: ABRIR CAIXA MIL-SPEC ---")
    caixa_aberta_confirmada = False
    erros_abertura = 0
    
    while not caixa_aberta_confirmada and state.executando:
        
        if erros_abertura > 10:
            print("🛑 Limite extremo de retentativas atingido (10x). Abortando Mil-Spec por segurança.")
            enviar_mensagem_telegram("⚠️ *Aviso:* Caixa Mil-Spec abortada (Muitos erros).", conta_nome)
            break

        try:
            if not pagina.locator(SELETOR_TELA_DE_BATALHA).is_visible(timeout=5000):
                clique_blindado(pagina, XPATH_BOTAO_VOLTAR, "Voltar")
                pagina.wait_for_selector(SELETOR_TELA_DE_BATALHA, state='visible', timeout=10000)
        except: 
            pagina.goto(URL_DO_JOGO, timeout=30000)
            time.sleep(4)
            gerir_popups(pagina)

        try:
            while state.executando:
                texto_dinheiro = pagina.locator(XPATH_DINHEIRO).inner_text()
                valor_em_string = re.sub(r'[^\d.]', '', texto_dinheiro)
                dinheiro_atual = int(float(valor_em_string) * 100) if valor_em_string else 0
                if dinheiro_atual >= CUSTO_CAIXA_FINAL: 
                    break 
                
                print(f"Dinheiro insuficiente ({dinheiro_atual / 100:.2f}). A vender um item...")
                tem_itens = vender_itens_continuamente(pagina, CUSTO_CAIXA_FINAL, conta_nome, e_rotina_final=True)
                
                if not tem_itens:
                     print("Sem itens para vender na rotina final.")
                     recolher_recompensas(pagina, conta_nome, verificacao_dura=False)
                     return
                     
                print("Recarregando para atualizar saldo final...")
                try: pagina.reload(wait_until='domcontentloaded', timeout=15000)
                except: pass
                time.sleep(3)
                
            if not state.executando: return
            
            print("A procurar caixa Mil-Spec...")
            caixa_final = pagina.locator(SELETOR_CAIXA_FINAL)
            for i in range(10): 
                if not state.executando: return
                if caixa_final.is_visible(): break
                pagina.mouse.wheel(0, 800) 
                time.sleep(random.uniform(1.0, 1.5)) 
                
            if not caixa_final.is_visible(): 
                raise Exception("Não foi possível encontrar a caixa.")
            
            print("Caixa 'Mil-Spec' encontrada!")
            caixa_final.click()
            time.sleep(2)
            
            txt_antes = pagina.locator(XPATH_DINHEIRO).inner_text()
            val_antes = re.sub(r'[^\d.]', '', txt_antes)
            saldo_antes = int(float(val_antes) * 100) if val_antes else 0
            
            botao_abrir = pagina.locator(SELETOR_BOTAO_ABRIR_CAIXA_FINAL)
            if not botao_abrir.is_visible(timeout=5000):
                print("⚠️ O botão Open não apareceu.")
                erros_abertura += 1
                aplicar_estrategia_recuperacao(pagina, erros_abertura)
                continue 
            
            botao_abrir.click()
            print("Botão de abrir clicado. Aguardando animação...")
            time.sleep(10)
            
            print("Recarregando página (F5) para confirmar abertura...")
            pagina.reload(wait_until='domcontentloaded', timeout=20000)
            time.sleep(5)
            gerir_popups(pagina) 
            
            try:
                txt_depois = pagina.locator(XPATH_DINHEIRO).inner_text()
                val_depois = re.sub(r'[^\d.]', '', txt_depois)
                saldo_depois = int(float(val_depois) * 100) if val_depois else 0
                
                if saldo_depois <= (saldo_antes - CUSTO_CAIXA_FINAL):
                    print(f"✅ Caixa Mil-Spec aberta e confirmada! (Saldo: {saldo_antes} -> {saldo_depois})")
                    caixa_aberta_confirmada = True 
                else:
                    print(f"⚠️ Saldo INALTERADO ({saldo_antes}). Abertura da Mil-Spec falhou.")
                    erros_abertura += 1
                    aplicar_estrategia_recuperacao(pagina, erros_abertura)
                    
            except Exception as e_verify:
                 print(f"Erro na verificação de saldo pós-abertura: {e_verify}")
                 erros_abertura += 1
                 aplicar_estrategia_recuperacao(pagina, erros_abertura)
                 
        except Exception as e:
            print(f"Erro na rotina final: {e}")
            erros_abertura += 1
            if recuperar_bot(pagina, URL_DO_JOGO, conta_nome): 
                continue 
            else: 
                enviar_mensagem_telegram("❌ *Bot:* Erro irrecuperável na rotina final (Mil-Spec).", conta_nome)
                break
                
    recolher_recompensas(pagina, conta_nome, verificacao_dura=True)
