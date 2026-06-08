# DESCRICAO: Monitoriza o pulso do bot (Lubuntu) e reinicia a VM se travar.

# Bloco de parametros (DEVE ser a primeira coisa executável do script)
param (
    [string]$AcaoFinal = "nenhuma" # Padrão: não faz nada com a energia, apenas fecha o Watchdog, desligar para desligar
)

# Se houver um erro fatal, nao fecha a janela imediatamente
trap {
    Write-Host "X ERRO CRITICO DO SISTEMA:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor White
    Read-Host "Pressione Enter para fechar e verificar o codigo"
    exit
}

# --- CONFIGURACOES - AJUSTE AQUI ---
# 1. Nome exato da sua maquina no VirtualBox
$nomeDaVM = "Bot Farmskin" 

# 2. Caminho da pasta no Windows
$caminhoHeartbeat = "" 

# 3. Tempos de seguranca
$tempoLimiteSegundos = 2700 
$tempoLimiteArranqueSegundos = 300 
$vboxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

# Variaveis de controle
$script:ultimoValorLido = ""
$script:modoManual = $false
$script:horaInicioScript = Get-Date

# --- LIMPEZA INICIAL ---
if (Test-Path $caminhoHeartbeat) {
    Remove-Item $caminhoHeartbeat -Force
}

# --- INICIO DO SCRIPT ---
Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   WATCHDOG ATIVO - MONITORANDO A VM: $nomeDaVM" -ForegroundColor Cyan
if ($AcaoFinal -ne "nenhuma") {
    Write-Host "   -> ACAO FINAL PROGRAMADA: $AcaoFinal O NOTEBOOK" -ForegroundColor Yellow
}
Write-Host "==========================================================" -ForegroundColor Cyan

# Verificacao de instalacao do VirtualBox
if (-not (Test-Path $vboxManage)) {
    Write-Host "X ERRO: Nao encontrei o VirtualBox em: $vboxManage" -ForegroundColor Red
    Read-Host "Pressione Enter para fechar"
    exit
}

Write-Host "Pasta de monitorizacao: $caminhoHeartbeat"
Write-Host "Aguardando o primeiro sinal do Bot..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------"

while ($true) {
    if (Test-Path $caminhoHeartbeat) {
        try {
            $conteudoRaw = (Get-Content $caminhoHeartbeat -Raw).Trim()
            
            # --- SINAIS ESPECIAIS ---
            if ($conteudoRaw -eq "SAIR") {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Bot terminou. A fechar o Watchdog..." -ForegroundColor Green
                
                # O GATILHO FINAL DE ENERGIA (Orquestração do Host)
                if ($AcaoFinal -eq "desligar") {
                    Write-Host "A desligar o notebook em 60 segundos..." -ForegroundColor Red
                    Write-Host "(Para cancelar, abra o CMD e digite: shutdown /a)" -ForegroundColor DarkGray
                    # /s = shutdown, /f = force (fecha tudo aberto), /t 60 = espera 60 segundos
                    shutdown /s /f /t 60
                }
                elseif ($AcaoFinal -eq "hibernar") {
                    Write-Host "A hibernar o notebook..." -ForegroundColor Cyan
                    Start-Sleep -Seconds 3 # Dá só um tempinho para a mensagem ser lida
                    # /h = hibernate
                    shutdown /h
                }
                else {
                    Write-Host "Nenhuma acao de energia solicitada. O notebook continuara ligado." -ForegroundColor Gray
                }
                
                exit
            }

            if ($conteudoRaw -eq "PAUSE") {
                if (-not $script:modoManual) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] MODO MANUAL - Vigilancia pausada." -ForegroundColor Cyan
                    $script:modoManual = $true
                }
                Start-Sleep -Seconds 30
                continue
            }

            # --- LOGICA DE MONITORAMENTO ---
            if ($conteudoRaw -match '^\d+$') {
                if ($script:modoManual) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pulso retomado! Vigilancia ativa." -ForegroundColor Green
                    $script:modoManual = $false
                }

                if ($conteudoRaw -ne $script:ultimoValorLido -and $script:ultimoValorLido -ne "") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pulso atualizado." -ForegroundColor Green
                }
                $script:ultimoValorLido = $conteudoRaw

                $lastPulse = [long]$conteudoRaw
                
                # Forma mais estavel de pegar o tempo Unix no Windows
                $epoch = New-Object DateTime 1970, 1, 1, 0, 0, 0, ([DateTimeKind]::Utc)
                $now = [int][Math]::Floor((Get-Date).ToUniversalTime().Subtract($epoch).TotalSeconds)
                
                $diff = $now - $lastPulse
                if ($diff -lt 0) { $diff = 0 }

                if ($diff -gt $tempoLimiteSegundos) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ! ALERTA: Travamento detectado!" -ForegroundColor Red
                    Start-Process -FilePath $vboxManage -ArgumentList "controlvm `"$nomeDaVM`" reset" -NoNewWindow -Wait
                    
                    # --- APÓS O RESET (Recomeça a contagem visual) ---
                    if (Test-Path $caminhoHeartbeat) { Remove-Item $caminhoHeartbeat -Force }
                    $script:ultimoValorLido = ""
                    $script:horaInicioScript = Get-Date
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🔄 VM Reiniciada. Retornando ao modo de espera (Boot)..." -ForegroundColor Yellow
                } else {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] OK - Bot ativo ($diff s / $tempoLimiteSegundos s)" -ForegroundColor Gray
                }
            }
        } catch {
            Write-Host "Erro na leitura. A tentar novamente..." -ForegroundColor DarkYellow
        }
    } else {
        # --- LOGICA DE BOOT ---
        $tempoPassado = (New-TimeSpan -Start $script:horaInicioScript -End (Get-Date)).TotalSeconds
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Aguardando boot... ($([math]::Round($tempoPassado)) s / $tempoLimiteArranqueSegundos s)" -ForegroundColor DarkGray

        if ($tempoPassado -gt $tempoLimiteArranqueSegundos) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] X Boot demorou demais. A reiniciar..." -ForegroundColor Red
            Start-Process -FilePath $vboxManage -ArgumentList "controlvm `"$nomeDaVM`" reset" -NoNewWindow -Wait
            
            # --- APÓS O RESET (Recomeça a contagem visual) ---
            if (Test-Path $caminhoHeartbeat) { Remove-Item $caminhoHeartbeat -Force }
            $script:horaInicioScript = Get-Date
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🔄 VM Reiniciada. Retornando ao modo de espera (Boot)..." -ForegroundColor Yellow
        }
    }
    
    # Diminuido para 30s para o terminal atualizar a mensagem de "Aguardando boot" mais rapidamente
    Start-Sleep -Seconds 30
}