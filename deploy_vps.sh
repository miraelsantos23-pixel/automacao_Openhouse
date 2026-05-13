#!/bin/bash

# --- CONFIGURAÇÃO DA VPS ---
VPS_USER="root"
VPS_IP="SEU_IP_AQUI"
VPS_PATH="/root/automacao-jetimob"
# ---------------------------

echo "🚀 Iniciando deploy para VPS ($VPS_IP)..."

# Compacta os arquivos necessários (evita enviar venv ou arquivos temporários)
tar --exclude='venv' --exclude='__pycache__' --exclude='.git' -czf deploy.tar.gz .

# Cria a pasta na VPS se não existir
ssh $VPS_USER@$VPS_IP "mkdir -p $VPS_PATH"

# Envia o arquivo compactado
scp deploy.tar.gz $VPS_USER@$VPS_IP:$VPS_PATH/

# Descompacta na VPS e remove o tar
ssh $VPS_USER@$VPS_IP "cd $VPS_PATH && tar -xzf deploy.tar.gz && rm deploy.tar.gz"

echo "✅ Arquivos enviados com sucesso para $VPS_PATH"
echo "💡 Para rodar na VPS: ssh $VPS_USER@$VPS_IP 'cd $VPS_PATH && docker-compose up -d --build'"

rm deploy.tar.gz
