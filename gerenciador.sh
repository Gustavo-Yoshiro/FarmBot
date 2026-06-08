#!/bin/bash
# DESCRIÇÃO: Controla a fila de contas, faz retentativas e gera o relatório final.


# --- Configuração de Caminhos ---
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"
CONTAS_FILE="$SCRIPT_DIR/contas.txt"
COMPLETED_FILE="$SCRIPT_DIR/contas_concluidas.txt"
DATA_FILE="$SCRIPT_DIR/ultima_data.txt" 
RELOGIN_FILE="$SCRIPT_DIR/contas_relogin.txt"
VENV_ACTIVATE="$SCRIPT_DIR/venv/bin/activate"

# --- Configurações do Telegram ---
TELEGRAM_TOKEN=""
TELEGRAM_CHAT_ID=""

enviar_telegram_simples() {
    local msg="$1"
    # Usa Python para fazer o URL Encode
    encoded_msg=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$msg")
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
         -d "chat_id=$TELEGRAM_CHAT_ID" \
         -d "text=$encoded_msg" \
         -d "parse_mode=Markdown" > /dev/null
}

# --- Função de Reset ---
fazer_reset() {
    rm -f "$COMPLETED_FILE"
    rm -f saldo_inicial_*.txt
    rm -f "$RELOGIN_FILE"
    
    if [ -f "$CONTAS_FILE" ]; then
        awk '!seen[$0]++' "$CONTAS_FILE" > "${CONTAS_FILE}.tmp" && mv "${CONTAS_FILE}.tmp" "$CONTAS_FILE"
        echo "📋 Lista de contas limpa (duplicatas removidas)."
    fi
    echo "🧹 Histórico completo resetado."
}

# --- Lógica de Reset Manual ---
if [ "$1" == "--reset" ]; then
    fazer_reset
    date +%F > "$DATA_FILE"
    echo "Gerenciador resetado manualmente. A iniciar do zero."
    exit 0
fi

# --- Lógica de Reset AUTOMÁTICO (Novo Dia) ---
HOJE=$(date +%F)
if [ -f "$DATA_FILE" ]; then ULTIMA_DATA=$(cat "$DATA_FILE"); else ULTIMA_DATA=""; fi

if [ "$HOJE" != "$ULTIMA_DATA" ]; then
    echo "========================================================"
    echo "📅 NOVO DIA DETETADO! ($HOJE)"
    echo "O gerenciador vai reiniciar o progresso automaticamente."
    echo "========================================================"
    fazer_reset
    echo "$HOJE" > "$DATA_FILE"
else
    echo "📅 Data atual: $HOJE (Continuação da execução de hoje)"
fi

# --- Ativação do Ambiente Virtual ---
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "Erro: Ambiente virtual não encontrado em '$VENV_ACTIVATE'"
    exit 1
fi
source "$VENV_ACTIVATE"
echo "Ambiente virtual ativado."

echo ">>> INICIANDO GERENCIADOR DE CONTAS <<<"
enviar_telegram_simples "🚀 *Iniciando operações do dia!* ($HOJE)"

# Limpa o arquivo de relogin no início da execução
rm -f "$RELOGIN_FILE"

while IFS= read -r conta || [[ -n "$conta" ]]; do
    if [ -z "$conta" ]; then continue; fi

    # 1. Verifica se já foi concluída
    if [ -f "$COMPLETED_FILE" ] && grep -Fxq "$conta" "$COMPLETED_FILE"; then
        echo "A conta '$conta' já foi processada com sucesso hoje. A saltar..."
        continue
    fi

    # 2. Verifica se já está na fila de relogin
    if [ -f "$RELOGIN_FILE" ] && grep -Fxq "$conta" "$RELOGIN_FILE"; then
        echo "A conta '$conta' aguarda relogin manual. A saltar..."
        continue
    fi

    echo "========================================================"
    echo "A iniciar o bot para a conta: $conta (Máx 3 Tentativas)"
    echo "========================================================"
    
    final_exit_code=1

    for ((tentativa=1; tentativa<=3; tentativa++)); do
        echo "--- Tentativa $tentativa de 3 para a conta '$conta' ---"
        
        set -o pipefail
        # O xvfb-run abre o navegador virtual
        BOT_OUTPUT=$(xvfb-run -a -n 99 -s "-screen 0 1280x720x24" python3 -u main.py "$conta" 2>&1 | tee /dev/tty)
        exit_code=$?
        set +o pipefail
        
        final_exit_code=$exit_code
        
        echo ">> Código de saída detectado: $exit_code"

        if [ $exit_code -eq 0 ]; then
            echo "Sucesso na tentativa $tentativa."
            break 
        fi

        if [ $exit_code -ge 2 ] && [ $exit_code -le 5 ]; then
            echo "Código especial ($exit_code). Encerrando tentativas."
            break 
        fi
        
        if [ $tentativa -lt 3 ]; then
            echo "Falha (código $exit_code). A aguardar 10s..."
            sleep 10
        else
            echo "Todas as 3 tentativas falharam."
        fi
    done
    
    case $final_exit_code in
        0)
            echo "✅ SUCESSO."
            echo "$conta" >> "$COMPLETED_FILE"
            ;;
        3)
            echo "⌛️ SESSÃO EXPIRADA. Adicionando à fila de Relogin Manual."
            echo "$conta" >> "$RELOGIN_FILE"
            ;;
        4)
            echo "⛔ STOP LOSS TOTAL. Concluído."
            # CORREÇÃO: Agora o script marca a conta como concluída para não repetir hoje!
            echo "$conta" >> "$COMPLETED_FILE"
            ;;
        5)
            echo "🔄 PREJUÍZO PARCIAL (Pular Conta)."
            # NOTA: Se você quiser que o Stop Loss Parcial também finalize a conta pro dia todo
            # mude a linha abaixo de "$CONTAS_FILE" para "$COMPLETED_FILE".
            # No momento, ele joga a conta para o fim da fila para tentar de novo hoje.
            echo "$conta" >> "$CONTAS_FILE"
            ;;
        6)
            echo "🔄 TIMEOUT. Final da fila."
            echo "$conta" >> "$CONTAS_FILE"
            ;;
        *)
            echo "❌ ERRO/OUTRO ($final_exit_code)."
            ;;
    esac
    sleep 5
done < "$CONTAS_FILE"

# --- FASE 2: RELOGIN MANUAL ---
if [ -f "$RELOGIN_FILE" ] && [ -s "$RELOGIN_FILE" ]; then
    echo ""
    echo "########################################################"
    echo "### INICIANDO FASE DE RELOGIN MANUAL (COM TELA) ###"
    echo "########################################################"
    echo "As seguintes contas precisam de login:"
    cat "$RELOGIN_FILE"
    echo "--------------------------------------------------------"
    
    awk '!seen[$0]++' "$RELOGIN_FILE" > "${RELOGIN_FILE}.tmp" && mv "${RELOGIN_FILE}.tmp" "$RELOGIN_FILE"

    while IFS= read -r conta_relogin || [[ -n "$conta_relogin" ]]; do
        echo ">>> ABRINDO TELA PARA: $conta_relogin <<<"
        
        python3 -u main.py "$conta_relogin" relogin < /dev/tty
        
        echo "Sessão salva. Iniciando automação em background..."

        set -o pipefail
        xvfb-run -a -n 99 -s "-screen 0 1280x720x24" python3 -u main.py "$conta_relogin" 2>&1 | tee /dev/tty
        exit_code=$?
        set +o pipefail

        if [ $exit_code -eq 0 ]; then
            echo "✅ $conta_relogin finalizada com sucesso."
            echo "$conta_relogin" >> "$COMPLETED_FILE"
        else
            echo "⚠️ $conta_relogin terminou com código $exit_code."
        fi

        echo "--------------------------------------------------------"
        sleep 5
    done < "$RELOGIN_FILE"
    
    rm -f "$RELOGIN_FILE"
fi

# ========================================================
# RELATÓRIO FINAL DA BANCA
# ========================================================
echo ">>> GERANDO RELATÓRIO FINAL DIÁRIO (LUCROS E SALDOS) <<<"
# O MODO AUTO manda Diário todo dia, Semanal no Domingo, Mensal no fim do mês!
python3 relatorios.py auto

echo ">>> FIM DO GERENCIADOR <<<"
echo "Gerenciador encerrado."
