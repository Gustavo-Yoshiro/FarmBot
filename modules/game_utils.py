# DESCRIÇÃO: Funções auxiliares partilhadas (leitura de cristais, recuperações).
import time
import re
from modules.config import *
from modules.navigation import clique_blindado, gerir_popups

def ler_quantidade_cristais(pagina):
    """Lê a quantidade atual de cristais no cabeçalho."""
    try:
        elemento = pagina.locator(XPATH_CRISTAIS).first
        if not elemento.is_visible():
            try: elemento.wait_for(state="visible", timeout=3000)
            except: pass
            
        if elemento.is_visible():
            texto = elemento.inner_text()
            valor_limpo = re.sub(r'[^\d]', '', texto)
            return int(valor_limpo) if valor_limpo else 0
    except Exception as e:
        print(f"Aviso: Não foi possível ler os cristais: {e}")
    return 0

def aplicar_estrategia_recuperacao(pagina, tentativa):
    """
    Alterna entre diferentes métodos de recarregar a página para evitar 
    que o bot fique preso no mesmo bug/cache visual infinitamente.
    """
    estrategia = (tentativa % 3)
    print(f"\n🔄 Acionando ESTRATÉGIA DE RECUPERAÇÃO VARIADA (Nível {estrategia}):")
    
    if estrategia == 1:
        print("-> Estratégia 1: Recarregamento Simples (F5)")
        try: pagina.reload(wait_until='domcontentloaded', timeout=20000)
        except: pass
        
    elif estrategia == 2:
        print("-> Estratégia 2: Navegação forçada para URL Base")
        try: pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=30000)
        except: pass
        
    else: # estrategia == 0
        print("-> Estratégia 3: Reset Profundo (Acessar perfil e voltar)")
        try:
            clique_blindado(pagina, XPATH_3_PONTOS, "Menu")
            time.sleep(1)
            clique_blindado(pagina, XPATH_BOTAO_PERFIL, "Perfil")
            time.sleep(4)
            pagina.goto(URL_DO_JOGO, wait_until='domcontentloaded', timeout=30000)
        except: pass
        
    time.sleep(6)
    gerir_popups(pagina)
