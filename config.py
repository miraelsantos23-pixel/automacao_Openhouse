import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv()

# Chave da API Jetimob
WEBSERVICE_KEY = os.getenv("JETIMOB_WEBSERVICE_KEY")

# Ceredenciais Canal PRO
EMAIL = os.getenv("CANALPRO_EMAIL")
PASSWORD = os.getenv("CANALPRO_PASSWORD")

JETIMOB_EMAIL = os.getenv("JETIMOB_EMAIL")
JETIMOB_PASSWORD = os.getenv("JETIMOB_PASSWORD")
# URLs
API_BASE_URL = "https://api.jetimob.com/webservice"
CANALPRO_CREATE_URL = "https://canalpro.grupozap.com/ZAP_OLX/0/listings/create"
JETIMOB_URL = "https://app.jetimob.com/imoveis?unidade_medida=m%C2%B2&origem=0"

# Arquivos
JETIMOB_PROGRESS_JSON = "./jetimob_progresso.json"
JETIMOB_REPORT_TXT = "./relatorio_execucao.txt"
DEFAULT_IMOVEIS_JSON = "./imoveis.json"
JETIMOB_ERROS_JSON = "./jetimob_erros.json"

# Timeouts e delays (em segundos)
REQUEST_TIMEOUT = 40
PAGE_LOAD_DELAY = 2
ELEMENT_WAIT_TIMEOUT = 7
ACTION_DELAY = 0
BETWEEN_IMOVEIS_DELAY = 1

