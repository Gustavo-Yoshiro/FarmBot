
---

# 🤖 FarmBot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PowerShell-5391FE?style=for-the-badge&logo=powershell&logoColor=white" alt="PowerShell" />
  <img src="https://img.shields.io/badge/VirtualBox-183A61?style=for-the-badge&logo=virtualbox&logoColor=white" alt="VirtualBox" />
  <img src="https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram API" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License MIT" />
</p>

> Um ecossistema completo de automação web projetado para rodar isolado numa Máquina Virtual (Lubuntu) com monitorização externa, orquestração de energia pelo Host (Windows) e relatórios via Telegram.

⚠️ **AVISO IMPORTANTE (DISCLAIMER):** Este projeto resultou no banimento das contas utilizadas na plataforma alvo devido aos sistemas rigorosos de anti-bot (Cloudflare, deteção de Webdriver e padrões de rede). O código está publicado **exclusivamente para fins educacionais e de estudo** sobre automação web, gestão de risco de estado e orquestração de Máquinas Virtuais.

---

## 📖 Sobre o Projeto

### 🎯 O que o App faz?
O **FarmBot** automatiza a navegação, login, coleta de recompensas diárias e batalhas em sites de "drop" de caixas. Ele possui uma lógica matemática de **Gestão de Risco** (Stop Loss Diário) e um sistema de **"Modo de Sobrevivência"** que calcula quantas tentativas o bot tem para recuperar o saldo antes de declarar falência.

### 📱 Alertas e Relatórios via Telegram
O sistema conta com uma integração nativa com a API do Telegram (`modules/telegram.py`) que envia notificações em tempo real:
* **Alertas Críticos:** Avisos instantâneos de falência, sessões expiradas ou erros de navegador.
* **Relatórios Financeiros:** Resumos de Lucro/Prejuízo e saldo atual ao fim do expediente.
* **Calendário Inteligente:** Fechamentos Diários, Semanais e Mensais automáticos.

---

## 🏗️ Arquitetura e Funcionamento

O projeto opera em um modelo de **mestre-escravo** entre o sistema Host e a Máquina Virtual, garantindo resiliência e economia de energia.

### 1. O Gerenciador (Guest - Bash/Python)
O arquivo `gerenciador.sh` atua como o orquestrador dentro do Linux:
* **Fila de Processamento:** Lê o arquivo `contas.txt` e inicia o bot para cada linha sequencialmente.
* **Sistema de Heartbeat:** Atualiza constantemente um sinal de vida ("pulso") que é lido pelo Host.
* **Finalização Segura:** Ao processar todas as contas, sinaliza o encerramento para que o Host possa agir.

### 2. O Watchdog (Host - PowerShell)
O `watchdog_virtualbox.ps1` vigia a VM pelo Windows:
* **Monitorização Externa:** Verifica via `VBoxManage` se a VM travou ou se o processo terminou.
* **Recuperação de Falhas:** Caso o bot trave no Linux, o Watchdog reinicia a VM forçadamente.
* **Gestão de Energia:** Desliga ou hiberna o computador físico assim que o trabalho termina.

---

## ⚙️ Instruções de Instalação (Setup)

**Pré-requisitos:**
* VirtualBox instalado no Host (`VBoxManage` no PATH).
* Python 3.10+ instalado no Guest (VM).

#### 1. Configurando a Máquina Virtual (Guest)
```bash
# Clone o repositório
git clone [https://github.com/Gustavo-Yoshiro/FarmBot.git](https://github.com/Gustavo-Yoshiro/FarmBot.git)
cd FarmBot

# Setup do ambiente Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium


#### 2. Configurando o Telegram

Edite os arquivos `modules/config.py` e `relatorios.py` com suas chaves:

* `TELEGRAM_TOKEN`: Token do seu Bot no BotFather.
* `TELEGRAM_CHAT_ID`: O seu ID de usuário.

---

## 🚀 Instruções de Uso

Siga a ordem exata abaixo para garantir a sincronia dos sistemas:

### Passo 1: Preparar as Contas (Guest)

Crie o arquivo `contas.txt` na raiz do projeto dentro da VM e adicione os dados de acesso, um por linha.

### Passo 2: Iniciar o Gerenciador (Guest)

No terminal do Linux (Lubuntu), execute:

```bash
chmod +x gerenciador.sh
./gerenciador.sh

```

### Passo 3: Ativar o Watchdog (Host)

Abra o **PowerShell como Administrador** no Windows e escolha como o PC deve se comportar ao finalizar:

```powershell
# Opção A: Apenas monitoriza (PC continua ligado)
.\watchdog_virtualbox.ps1 -AcaoFinal nenhuma

# Opção B: Desliga o PC automaticamente ao terminar
.\watchdog_virtualbox.ps1 -AcaoFinal desligar

# Opção C: Hiberna o PC ao terminar
.\watchdog_virtualbox.ps1 -AcaoFinal hibernar

```

---

## 🧠 Lições Aprendidas (Post-Mortem)

Este projeto foi um laboratório para entender as barreiras de automação modernas:

* **Assinatura do Navegador:** Necessidade de contornar a flag `navigator.webdriver`.
* **Reputação de IP:** A importância de Proxies ISP para evitar bans por densidade de acessos.
* **Fingerprinting:** Como sistemas de rede detectam padrões de comportamento não-humanos.

---

## ✨ Contribuidores / Autores

Feito com dedicação por **Gustavo Yoshiro**.

* [Meu LinkedIn](https://www.google.com/search?q=https://www.linkedin.com/in/gustavosaitodev)
* [Meu GitHub](https://www.google.com/search?q=https://github.com/Gustavo-Yoshiro)

---

📝 Licença: [MIT](https://www.google.com/search?q=LICENSE)
