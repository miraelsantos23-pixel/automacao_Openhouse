# Use a imagem base oficial do Python
FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=1
ENV DISPLAY=:99

# Instala dependências do sistema para Firefox, Selenium e Tkinter
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    bzip2 \
    python3-tk \
    xvfb \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Instala o Geckodriver (necessário para o Firefox no Selenium)
RUN GECKODRIVER_VERSION=$(wget -qO- https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep -Po '"tag_name": "\K.*?(?=")') \
    && wget -q "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" \
    && tar -xzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

# Define o diretório de trabalho
WORKDIR /app

# Copia os requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da automação
COPY . .

# Cria um script de entrada para rodar o Xvfb (display virtual) e a aplicação
# Isso é necessário porque o código usa Tkinter para exibir mensagens, mesmo que em modo oculto
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1024x768x16 &\n\
sleep 2\n\
python main.py "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Define o script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
