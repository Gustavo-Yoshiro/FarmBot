# ==============================================================================
# ARQUIVO: modules/setup.py
# DESCRIÇÃO: Inicialização do navegador, contexto furtivo e verificação de login inicial.
# ==============================================================================
import os
import sys
import time
import modules.state as state
from modules.config import *
from modules.telegram import enviar_mensagem_telegram
from modules.auth import tentar_login_automatico

def inicializar_navegador(p, conta_nome):
    """
    Configura e lança o navegador com opções stealth.
    Retorna: navegador, contexto, pagina
    """
    navegador = p.firefox.launch(
        headless=False, 
        slow_mo=100,
        # Preferência nativa do Firefox para esconder que é automatizado
        firefox_user_prefs={
            "dom.webdriver.enabled": False
        }
    )
    
    arquivo_sessao = f"{conta_nome}.json"
    contexto = None
    
    if os.path.exists(arquivo_sessao):
        print(f"Ficheiro de sessão '{arquivo_sessao}' encontrado. A carregar...")
        contexto = navegador.new_context(
            storage_state=arquivo_sessao,
            ignore_https_errors=True
        )
    else:
        print(f"Iniciando contexto limpo para '{conta_nome}'.")
        contexto = navegador.new_context(ignore_https_errors=True)
    
    contexto.add_init_script("""
        // 1. Sobrescreve a propriedade webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 2. Simula idiomas reais de um usuário
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en']
        });
        
        // 3. Falsifica a presença de plugins (bots costumam não ter plugins)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)

    pagina = contexto.new_page()
    pagina.set_default_timeout(45000) 
    
    return navegador, contexto, pagina

def verificar_acesso_inicial(pagina, contexto, conta_nome, forcar_relogin):
    """
    Navega para o site e garante que o estado de login seja detectado corretamente.
    Usa Polling (verificação repetida) para ser mais robusto em VMs lentas.
    """
    arquivo_sessao = f"{conta_nome}.json"
    
    try:
        print(f"Navegando para {URL_DO_JOGO}...")
        pagina.goto(URL_DO_JOGO, timeout=60000, wait_until='domcontentloaded')
        
        # --- 1. MODO LOGIN MANUAL ---
        if forcar_relogin:
            print("="*50)
            print(f"Janela aberta para a conta '{conta_nome}'.")
            print("⚠️ MODO RELOGIN MANUAL ATIVO ⚠️")
            
            try:
                input(">>> Pressione ENTER neste terminal APÓS concluir o login... <<<")
            except EOFError:
                print("\n❌ ERRO: Terminal não interativo detectado. Abortando.")
                state.bot_exit_code = 1
                return False
            
            try:
                # Verifica se logou (botão de login deve ter sumido)
                if pagina.locator(SELETOR_BOTAO_LOGIN).is_visible(timeout=3000):
                    print("Aviso: Botão de login ainda visível. Salvando sessão mesmo assim...")
                
                contexto.storage_state(path=arquivo_sessao)
                print(f"✅ Nova sessão guardada em '{arquivo_sessao}'!")
                print("Fechando para reiniciar em modo oculto...")
                return False 
            except Exception as e:
                print(f"Erro ao salvar sessão: {e}")
                return False

        # --- 2. VERIFICAÇÃO INTELIGENTE DE ESTADO (POLLING) ---
        print("Aguardando carregamento da interface (Procurando Login ou Perfil)...")
        
        # Listas de seletores para tentar (do mais específico ao mais genérico)
        seletores_login_check = [
            SELETOR_BOTAO_LOGIN,           # .signin (Do config)
            "button:has-text('SIGN IN')",  # Texto exato maiúsculo
            "text='Sign In'",              # Texto genérico
            "text='Login'",                # Texto genérico
            # XPath específico fornecido anteriormente (backup)
            "xpath=//*[@id='app']/div/div[1]/div[1]/header/div/div/div[2]/div[2]/div[2]/div[1]/button"
        ]
        
        seletores_perfil_check = [
            XPATH_BOTAO_PERFIL,
            ".profile-header__burger",     # Menu sanduíche (aparece quando logado)
            ".profile-header__avatar"      # Avatar (aparece quando logado)
        ]
        
        login_visivel = False
        perfil_visivel = False
        
        # Loop de Polling: Tenta identificar o estado por 30 segundos
        start_time = time.time()
        estado_identificado = False
        
        while time.time() - start_time < 30:
            # Verifica Login
            for sel in seletores_login_check:
                if pagina.locator(sel).first.is_visible():
                    print(f"Botão de Login detectado pelo seletor: {sel}")
                    login_visivel = True
                    estado_identificado = True
                    break
            if estado_identificado: break

            # Verifica Perfil
            for sel in seletores_perfil_check:
                if pagina.locator(sel).first.is_visible():
                    print(f"Perfil detectado pelo seletor: {sel}")
                    perfil_visivel = True
                    estado_identificado = True
                    break
            if estado_identificado: break
            
            time.sleep(1) # Espera 1s e tenta de novo

        # Se não identificou nada, tenta F5 e mais uma rodada rápida
        if not estado_identificado:
            print("⚠️ Interface não carregou. Tentando Reload (F5)...")
            try:
                pagina.reload(wait_until='domcontentloaded', timeout=30000)
                time.sleep(3)
                
                # Polling rápido pós-reload (15s)
                start_time_2 = time.time()
                while time.time() - start_time_2 < 15:
                    for sel in seletores_login_check:
                        if pagina.locator(sel).first.is_visible():
                            login_visivel = True; estado_identificado = True; break
                    if estado_identificado: break
                    for sel in seletores_perfil_check:
                        if pagina.locator(sel).first.is_visible():
                            perfil_visivel = True; estado_identificado = True; break
                    if estado_identificado: break
                    time.sleep(1)
            except Exception as e_reload:
                print(f"Erro no reload: {e_reload}")

        # --- TOMADA DE DECISÃO ---
        if login_visivel:
            print("!!! SESSÃO EXPIRADA DETECTADA NO ARRANQUE !!!")
            
            if not os.path.exists(arquivo_sessao):
                print(f"⚠️ Arquivo de sessão '{arquivo_sessao}' não existe. Auto-login impossível.")
                state.bot_exit_code = 3
                return False

            # Tenta Login Automático
            if tentar_login_automatico(pagina, contexto, arquivo_sessao):
                print("✅ Recuperação de sessão automática bem sucedida!")
                return True 
            else:
                print("❌ Login automático falhou.")
                enviar_mensagem_telegram("⌛️ *Sessão Expirada (Arranque)!* Auto-login falhou.", conta_nome)
                state.bot_exit_code = 3
                return False
        
        elif perfil_visivel:
            print("✅ Login verificado (Perfil visível).")
            return True
            
        else:
            print("❌ Falha crítica: Não foi possível determinar o estado do login (Tela branca ou erro de carregamento).")
            # Timeout / Erro de carga
            state.bot_exit_code = 6 
            return False 

    except Exception as e:
        print(f"Erro crítico no arranque (Navegação): {e}")
        enviar_mensagem_telegram(f"❌ *Erro Crítico:* {e}", conta_nome)
        if "Timeout" in str(e) or "timeout" in str(e):
            state.bot_exit_code = 6
        else:
            state.bot_exit_code = 1
        return False
