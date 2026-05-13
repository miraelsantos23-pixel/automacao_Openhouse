# Automação Jetimob V2 - Guia de Execução e Deploy

![Run Jetimob Automation](https://github.com/miraelsantos23-pixel/automacao_Openhouse/actions/workflows/main.yml/badge.svg)

Este guia explica como rodar a automação localmente e como acompanhar a execução automática via GitHub Actions às 23:00 (GMT-3).

## 🍎 Executando no MacBook (macOS)

1. **Instale o Python 3.11+**: Caso não tenha, baixe no site oficial ou use `brew install python`.
2. **Instale o Geckodriver**:
   ```bash
   brew install geckodriver
   ```
3. **Instale o Firefox**: Certifique-se de que o Firefox está instalado na pasta Aplicativos.
4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Execute**:
   ```bash
   python main.py
   ```

---

## ☁️ Deploy na VPS (Linux) via Docker

A forma mais fácil de rodar na VPS é usando **Docker**, pois ele já configura o Firefox, Geckodriver e o agendamento automaticamente.

### 1. Preparar a VPS
Certifique-se de que a VPS tem o **Docker** e o **Docker Compose** instalados.

### 2. Subir os arquivos para a VPS
Você pode usar os scripts inclusos para facilitar o envio via SSH:

#### No Windows:
Edite o arquivo `deploy_vps.bat` com os dados da sua VPS e execute-o.

#### No macOS/Linux:
Edite o arquivo `deploy_vps.sh` com os dados da sua VPS e execute-o:
```bash
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### 3. Iniciar na VPS
Uma vez dentro da VPS, navegue até a pasta e rode:
```bash
docker-compose up -d --build
```

**Nota:** No modo VPS ou GitHub Actions, a automação executará todos os dias às **23:00 (GMT-3)**.

---

## 🕒 Agendamento
O sistema detecta automaticamente se está rodando em um ambiente Docker (`DOCKER_ENV=1`) e ativa o agendamento diário.
Se quiser forçar o modo de agendamento em qualquer sistema, use:
```bash
python main.py --vps
```