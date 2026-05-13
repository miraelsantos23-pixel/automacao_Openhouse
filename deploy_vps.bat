@echo off
setlocal

:: --- CONFIGURAÇÃO DA VPS ---
set VPS_USER=root
set VPS_IP=SEU_IP_AQUI
set VPS_PATH=/root/automacao-jetimob
:: ---------------------------

echo 🚀 Iniciando deploy para VPS (%VPS_IP%)...

:: Envia os arquivos via SCP (usando o scp nativo do Windows 10/11)
:: Nota: Isso assume que você tem permissão de escrita e o servidor SSH configurado
echo 📂 Enviando arquivos...
ssh %VPS_USER%@%VPS_IP% "mkdir -p %VPS_PATH%"

:: Envia arquivos principais
scp main.py %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp jetimob_automation.py %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp api_client.py %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp config.py %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp requirements.txt %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp Dockerfile %VPS_USER%@%VPS_IP%:%VPS_PATH%/
scp docker-compose.yml %VPS_USER%@%VPS_IP%:%VPS_PATH%/

echo ✅ Arquivos enviados com sucesso!
echo 💡 Para rodar na VPS: ssh %VPS_USER%@%VPS_IP% "cd %VPS_PATH% && docker-compose up -d --build"

pause
