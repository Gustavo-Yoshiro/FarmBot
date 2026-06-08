🤖 FarmBot

Um ecossistema completo de automação web projetado para rodar isolado numa Máquina Virtual (Lubuntu) com monitorização externa, orquestração de energia pelo Host (Windows) e relatórios via Telegram.

⚠️ AVISO IMPORTANTE (DISCLAIMER): Este projeto resultou no banimento das contas utilizadas na plataforma alvo devido aos sistemas rigorosos de anti-bot (Cloudflare, deteção de Webdriver e padrões de rede). O código está publicado exclusivamente para fins educacionais e de estudo sobre automação web, gestão de risco de estado e orquestração de Máquinas Virtuais.

📖 Sobre o Projeto

O que o App faz?

O FarmBot automatiza a navegação, login, coleta de recompensas diárias e batalhas em sites de "drop" de caixas (como o Farmskins). Ele possui uma lógica matemática de Gestão de Risco (Stop Loss Diário) e um sistema de "Modo de Sobrevivência" que calcula quantas tentativas o bot tem para recuperar o saldo antes de declarar falência.

A arquitetura é dividida em duas camadas principais e uma de comunicação:

Guest (Máquina Virtual): Roda a automação em si (Python).

Host (Máquina Física): Roda um "Watchdog" (Cão de Guarda em PowerShell) que monitoriza o sistema da VM e desliga/hiberna o computador físico ao terminar o expediente.

Comunicação (Telegram): Notifica o administrador em tempo real sobre o status financeiro e da infraestrutura.

📱 Alertas e Relatórios via Telegram

O sistema conta com uma integração nativa com a API do Telegram (modules/telegram.py e relatorios.py) que envia notificações diretamente para o celular do administrador:

Alertas Críticos: Avisos instantâneos caso a conta atinja falência (saldo zerado), sessão expirada, ou encontre erros irrecuperáveis no navegador.

Relatórios Financeiros: Resumos agregados automáticos enviados ao fim do expediente com o Lucro/Prejuízo Total, Saldo Atual de todas as contas e Alertas de Risco.

Calendário Inteligente: Gera automaticamente relatórios de fechamento Diário, Semanal (aos domingos) e Mensal (no último dia do mês).

Com o que foi construído?

Python 3: Linguagem principal da automação.

Playwright: Framework de automação web utilizado para navegação e injeção de scripts (Stealth).

PowerShell & Bash: Scripts para a orquestração e monitorização do sistema operativo.

Oracle VirtualBox: Utilizado como sandbox de segurança para esconder o HWID físico da máquina.

Por que foi construído?

Este projeto nasceu como um objeto de estudo intensivo para dominar:

Evasão básica de sistemas Anti-Bot e camuflagem de Webdriver.

Estruturas de State Machines (Máquinas de Estado) e programação tolerante a falhas (polling, fallbacks e heartbeats).

Integração e comunicação assíncrona entre sistemas operacionais diferentes (Host Windows e Guest Linux).

⚙️ Instruções de Instalação (Setup)

Para rodar este projeto, precisará de configurar os dois ambientes (Host e Guest).

Pré-requisitos:

VirtualBox instalado no Host (VBoxManage no PATH).

Python 3.10+ instalado no Guest (VM).

Git para clonar o repositório.

1. Configurando a Máquina Virtual (Guest)

# Clone este repositório
git clone [https://github.com/Gustavo-Yoshiro/FarmBot.git](https://github.com/Gustavo-Yoshiro/FarmBot.git)

# Acesse a pasta do projeto
cd FarmBot

# Crie e ative um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
playwright install chromium


Configuração do Telegram: Abra os arquivos modules/config.py e relatorios.py e insira o seu TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.

2. Configurando o Watchdog (Host)

Copie o arquivo watchdog_virtualbox.ps1 para a sua máquina Windows.

Altere as variáveis $nomeDaVM e $caminhoHeartbeat no topo do script para apontarem para as suas configurações locais.

🚀 Instruções de Uso

A operação ideal do sistema ocorre através do Gestor Principal (Bash) e do Watchdog (PowerShell).

No Linux (Guest): Iniciar a fila de contas
Execute o gerenciador em background para ler o ficheiro contas.txt:

./gerenciador.sh


No Windows (Host): Iniciar a monitorização e orquestração de energia
Abra o PowerShell como Administrador e escolha o comando que melhor atende o fim do seu expediente:

# Apenas monitoriza (deixa o PC ligado no final)
.\watchdog_virtualbox.ps1

# Monitoriza e DESLIGA o PC físico ao final das tarefas
.\watchdog_virtualbox.ps1 -AcaoFinal desligar

# Monitoriza e HIBERNA o PC físico ao final das tarefas
.\watchdog_virtualbox.ps1 -AcaoFinal hibernar


🤝 Como Contribuir

Contribuições são super bem-vindas, especialmente para tentar refinar as técnicas de Stealth (Evasão) com o Playwright! Para contribuir:

Faça um Fork do projeto.

Crie uma Branch para a sua feature (git checkout -b feature/NovaCamuflagem).

Faça o Commit das suas mudanças (git commit -m 'Adicionando bypass de Cloudflare').

Faça o Push para a branch (git push origin feature/NovaCamuflagem).

Abra um Pull Request.

🧠 Lições Aprendidas (Post-Mortem)

Apesar da automação funcionar perfeitamente a nível de software local, a plataforma alvo baniu as contas pelos seguintes fatores que merecem estudo para projetos futuros:

Assinatura do Navegador: O Playwright padrão levanta a flag navigator.webdriver = true.

IP Fixo: Múltiplas contas a aceder à plataforma a partir do mesmo IP residencial num curto espaço de tempo. O ideal seria o uso de Proxies ISP distribuídos.

Fingerprinting de Rede e Tela: Resoluções estáticas e falta de histórico de Cookies orgânicos a longo prazo.

📝 Licença

Este projeto está sob a licença MIT. Isso significa que você pode usá-lo, modificá-lo e distribuí-lo livremente, desde que dê os devidos créditos. Veja o arquivo LICENSE para mais detalhes.

✨ Contribuidores / Autores

Feito com dedicação e muita engenharia reversa por Gustavo Yoshiro.
Se quiser trocar uma ideia sobre automação, cibersegurança ou arquitetura de software, sinta-se à vontade para me contatar!

