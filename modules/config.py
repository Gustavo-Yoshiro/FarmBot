# DESCRIÇÃO: Contém todas as constantes, credenciais e seletores do bot.


# Configurações do Telegram 
# PREENCHA COM AS SUAS INFORMAÇÕES
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Configurações Gerais do Jogo 
URL_DO_JOGO = "https://farmskins.com"
CUSTO_DA_BATALHA = 29       # Custo para entrar na batalha (centavos)
CUSTO_CAIXA_FINAL = 29      # Custo da caixa final (centavos)

# Limites de Gestão de Banca (Stop Loss)
# Valores em cêntimos (ex: -100 = -$1.00)
LIMITE_PULA_CONTA = -100    # Se atingir, pula para o final da fila (tentar mais tarde)
LIMITE_PARA_CONTA = -200    # Se atingir, para a conta por hoje

# Seletores de Interface (CSS e XPath) 

# Login e Header
SELETOR_BOTAO_LOGIN = '.signin' 
XPATH_DINHEIRO = '//*[@id="app"]/div/div[1]/div[1]/header/div[1]/div/div[2]/div[1]/a[3]/div[2]/a/span'
XPATH_CRISTAIS = '//*[@id="app"]/div/div[1]/div[1]/header/div[1]/div/div[2]/div[1]/a[1]/span'

# Navegação Principal
SELETOR_TELA_DE_BATALHA = 'a.fixed-menu.wrapper-casebattles[href="/casebattle/active"]'
XPATH_BOTAO_VOLTAR = '//*[@id="app"]/div/div[1]/div[1]/header/div[1]/div/div[1]/a'

# Menu e Perfil
XPATH_3_PONTOS = '.profile-header__burger'  
XPATH_BOTAO_PERFIL = '//*[@id="app"]/div/div[1]/div[1]/header/div[1]/div/div[2]/div[2]/div[2]/div[2]/a[1]'

# Batalha (Farm Zone)
XPATH_CRIAR_BATALHA = '//*[@id="app"]/div/div[1]/div[3]/div/div/div[3]/div[2]/button'
SELETOR_CAIXA_PARA_BATALHA = '.cases-modal__case:has-text("Mil-Spec")'
XPATH_CONFIRMAR_BATALHA = '//*[@id="modals-container"]/div/div[2]/div/div[3]/button'
XPATH_BOTAO_INICIAR_BATALHA = '//*[@id="app"]/div/div[1]/div[3]/div/div/div[4]/button'
SELETOR_VITORIA = ".win"
SELETOR_DERROTA = ".lose"
XPATH_X_FECHAR_RESULTADO = '//*[@id="modals-container"]/div/div[2]/div/button'

# Inventário e Vendas
SELETOR_FILTRO_ALL = 'text="All"'
SELETOR_FILTRO_ACTIVE = 'text="Active"' 
SELETOR_DA_SKIN_PARA_VENDER = '.skin-card'
SELETOR_BOTAO_VENDA = 'div.item-manager__button:has-text("Sell for")'
SELETOR_BOTAO_CONFIRMAR_VENDA = '#modals-container button:text-matches("Sell", "i")'
SELETOR_BOTAO_SELL_ALL = '.profile-my-skins__sell-all-button'

# Missões Diárias
SELETOR_RECOMPENSAS_DIARIAS = 'span.base-tabs__tab:has-text("Daily Reward")'
SELETOR_TEXTO_MISSAO = 'div.daily-reward-task__text:has-text("Win in a Farm Zone 3 times in a row")'
SELETOR_BOTAO_GET_REWARD = 'button.daily-reward-task__btn:has-text("Get reward"):not([disabled]):not(.disabled)'

# Caixa Final
SELETOR_CAIXA_FINAL = 'a[href="/classic-mil-spec"]'
SELETOR_BOTAO_ABRIR_CAIXA_FINAL = 'button:has-text("OPEN CASE")'

# Autenticação Steam
SELETOR_BOTAO_STEAM_LOGIN = '#imageLogin' 

# Outros
SELETOR_OVERLAY_POPUP = '.vm--overlay'
