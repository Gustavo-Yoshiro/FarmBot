# DESCRIÇÃO: Lógica para renovação de sessão, login automático e logout (teste).
import time
from modules.config import *
from modules.navigation import clique_blindado, gerir_popups

def tentar_login_automatico(pagina, contexto, arquivo_sessao):
    """
    Tenta renovar a sessão clicando em Sign In e confirmando na Steam.
    Confia puramente em elementos visuais, ignorando a URL.
    """
    print("🔄 Tentativa de Login Automático...")
    
    try:
        # 1. Clicar no botão de Login no Farmskins
        if not clique_blindado(pagina, SELETOR_BOTAO_LOGIN, "Botão Sign In (Farmskins)"):
            print("Falha ao clicar no botão de login inicial.")
            return False
        
        # 2. Aguardar botão da Steam (Sem esperar URL)
        print("Aguardando botão 'Iniciar sessão' da Steam...")
        try:
            # Timeout 60s para garantir carregamento
            pagina.wait_for_selector(SELETOR_BOTAO_STEAM_LOGIN, state='visible', timeout=60000)
            print("Botão da Steam detectado!")
        except Exception as e:
            print(f"Erro: Botão da Steam não apareceu. Continuando para verificação...")
            return False
        
        # 3. Interagir na página da Steam
        try:
            botao_steam = pagina.locator(SELETOR_BOTAO_STEAM_LOGIN)
            botao_steam.scroll_into_view_if_needed()
            time.sleep(0.5) 
            
            # Clica no botão verde da Steam
            botao_steam.click()
            print("Botão da Steam clicado! Aguardando retorno...")
            
            
        except Exception as e_steam:
            print(f"Erro na interação com a Steam: {e_steam}")
            return False

        print("Verificando sucesso do login (Polling Rápido)...")
        
        # 4. LOOP DE VERIFICAÇÃO DE SUCESSO (Otimizado)
        start_time = time.time()
        login_sucesso = False
        
        # Verifica por 60 segundos (aumentado para garantir retorno lento)
        while time.time() - start_time < 60:
            # Indicador A: Saldo apareceu? (Prioridade)
            if pagina.locator(XPATH_DINHEIRO).first.is_visible():
                print("✅ Saldo detectado! Login confirmado.")
                login_sucesso = True
                break
            
            # Indicador B: Perfil apareceu?
            if pagina.locator(XPATH_BOTAO_PERFIL).first.is_visible():
                print("✅ Perfil detectado! Login confirmado.")
                login_sucesso = True
                break
                
            # Indicador C: Botão de Login SUMIU?
            # Se o botão de login sumir e o site carregou, é bom sinal.
            try:
                if not pagina.locator(SELETOR_BOTAO_LOGIN).first.is_visible():
                    # Pequena confirmação rápida
                    time.sleep(1.0)
                    if not pagina.locator(SELETOR_BOTAO_LOGIN).first.is_visible():
                        # Só confirma se tiver algum outro elemento do site visível (pra não ser tela branca)
                        if pagina.locator(".footer").first.is_visible() or pagina.locator(".header").first.is_visible():
                            print("✅ Botão de login desapareceu e site carregou! Login confirmado.")
                            login_sucesso = True
                            break
            except:
                pass
            
            time.sleep(0.5)

        if login_sucesso:
            try:
                contexto.storage_state(path=arquivo_sessao)
            except:
                pass
            return True
        else:
            print("❌ Tempo esgotado. O login parece ter falhado.")
            return False

    except Exception as e:
        print(f"Erro crítico durante login automático: {e}")
        return False

# FUNÇÃO DE TESTE / UTILITÁRIA 
def teste_deslogar_conta(pagina):
    """
    Função de teste para deslogar da conta.
    Usa Zoom Out para garantir visibilidade.
    """
    print("\n--- 🧪 INICIANDO TESTE DE LOGOUT ---")
    
    try:
        gerir_popups(pagina)
        
        print("Abrindo menu...")
        if not clique_blindado(pagina, XPATH_3_PONTOS, "Menu (3 Pontos)"):
            print("❌ Falha ao abrir o menu para deslogar.")
            return

        time.sleep(1.5) 
        
        print("Aplicando Zoom Out de 50%...")
        try:
            pagina.evaluate("document.body.style.zoom = '0.5'")
            time.sleep(1.0)
        except:
            pass

        print("Procurando botão de logout...")
        
        # Seletor por ícone (mais estável)
        seletor_icone = 'a.profile-menu__nav-item:has(use[href*="logout"])'
        seletor_texto = "a.profile-menu__nav-item:has-text('Sair')"
        
        sucesso = False
        if clique_blindado(pagina, seletor_icone, "Botão Sair (Ícone)"):
            sucesso = True
        elif clique_blindado(pagina, seletor_texto, "Botão Sair (Texto)"):
            sucesso = True
            
        # Restaura zoom
        try:
            pagina.evaluate("document.body.style.zoom = '1'")
        except:
            pass

        if sucesso:
            print("Clique de logout realizado. Verificando...")
            time.sleep(3)
            if pagina.locator(SELETOR_BOTAO_LOGIN).is_visible(timeout=10000):
                print("✅ SUCESSO: Conta deslogada.")
            else:
                print("⚠️ AVISO: Não consegui confirmar o logout.")
        else:
            print("❌ FALHA: Botão de sair não encontrado.")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    finally:
        try:
            pagina.evaluate("document.body.style.zoom = '1'")
        except:
            pass
