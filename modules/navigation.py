# DESCRIÇÃO: Funções para interação com a página (cliques, recuperação, popups).

import time
import random
from modules.config import *
import modules.state as state
from modules.telegram import enviar_mensagem_telegram

def clique_blindado(pagina, seletor, nome_elemento):
    """
    Tenta clicar de forma humana primeiro (hover + click).
    Usa apenas clique nativo (force=True) sem injeção de JS.
    Retorna True se clicou, False se falhou.
    """
    # Verificação de segurança antes de tentar clicar
    if not state.executando: return False

    print(f"A acionar: {nome_elemento}...")
    try:
        elemento = pagina.locator(seletor).first
        
        # 1. Espera Visual (Aumentada para internet lenta)
        try:
            elemento.wait_for(state="visible", timeout=15000)
        except:
            print(f"Aviso: {nome_elemento} demorou a aparecer. Tentando interagir mesmo assim...")

        if not state.executando: return False

        # 2. Humanização: Tenta mover o mouse para cima do elemento
        try:
            elemento.hover(timeout=2000, force=True)
            time.sleep(random.uniform(0.1, 0.3)) 
        except:
            pass 

        # 3. Tenta clique nativo (Playwright)
        # Timeout aumentado para 10s para acomodar lentidão
        elemento.click(timeout=10000, force=True)
            
        time.sleep(random.uniform(0.5, 1.0)) 
        return True
    except Exception as e:
        print(f"Erro crítico ao tentar clicar em {nome_elemento}: {e}")
        return False

def recuperar_bot(pagina, url_jogo, conta_nome):
    """Tenta recuperar o bot de um estado de erro, retornando True em caso de sucesso."""
    print("A tentar recuperar o bot...")
    try:
        print("Tentativa 1: Navegar para a URL inicial...")
        # Timeout ajustado para 45s
        pagina.goto(url_jogo, timeout=45000, wait_until='domcontentloaded')
        print("✅ Recuperado com sucesso! A reiniciar o ciclo...")
        return True
    except Exception as goto_error:
        print(f"⚠️  Falhou. Última tentativa: Recarregar a página...")
        try:
            # Timeout ajustado para 45s
            pagina.reload(wait_until='domcontentloaded', timeout=45000)
            print("✅ Recuperado com sucesso! A reiniciar o ciclo...")
            return True
        except:
            print("❌ Não foi possível recuperar. A encerrar.")
            enviar_mensagem_telegram("❌ *Bot de Automação:* Erro crítico irrecuperável. O bot foi encerrado.", conta_nome)
            state.executando = False
            state.bot_exit_code = 1 
            return False

def gerir_popups(pagina):
    """Verifica se há um pop-up genérico (overlay) e clica nele para o fechar."""
    try:
        overlay = pagina.locator(SELETOR_OVERLAY_POPUP)
        # Timeout de 3s para dar tempo do popup aparecer
        if overlay.is_visible(timeout=3000): 
            print("Pop-up genérico detetado. Tentando fechar...")
            
            try:
                overlay.click(timeout=1000, force=True)
            except:
                pass
            
            # PLANO B: Pressionar ESC
            print("Enviando comando ESC...")
            pagina.keyboard.press("Escape")
            
            try:
                overlay.wait_for(state='hidden', timeout=5000)
                print("Pop-up fechado.")
            except:
                print("Aviso: O pop-up ainda consta como visível. Seguindo...")
            
            time.sleep(3.0) 
    except Exception:
        pass
