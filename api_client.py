"""
Cliente para comunicação com a API Jetimob
"""
import json
import os
from typing import Optional, Dict, Any, Union
import requests
from requests.exceptions import Timeout, RequestException

from config import WEBSERVICE_KEY, API_BASE_URL, DEFAULT_IMOVEIS_JSON, REQUEST_TIMEOUT


def fazer_requisicao(
    url: str,
    metodo: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    dados: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: Union[int, tuple] = REQUEST_TIMEOUT
) -> Dict[str, Any]:
    """
    Faz uma requisição HTTP para o endpoint especificado.
    
    Args:
        url: URL do endpoint
        metodo: Método HTTP (GET, POST, PUT, DELETE, etc.)
        headers: Cabeçalhos HTTP opcionais
        dados: Dados para enviar no corpo da requisição (form-data)
        json_data: Dados JSON para enviar no corpo da requisição
        timeout: Timeout em segundos ou tupla (connect_timeout, read_timeout)
    
    Returns:
        Dicionário com status_code, headers e dados da resposta
    """
    try:
        # Configuração padrão de headers
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        
        # Faz a requisição
        response = requests.request(
            method=metodo,
            url=url,
            headers=headers,
            data=dados,
            json=json_data,
            timeout=timeout
        )
        
        # Tenta parsear como JSON, se não conseguir retorna texto
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        resultado = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response_data,
            "success": response.status_code < 400
        }
        
        return resultado
        
    except Timeout as e:
        return {
            "success": False,
            "error": f"Timeout: {str(e)}",
            "status_code": None,
            "timeout": True
        }
    except RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": None,
            "timeout": isinstance(e, Timeout)
        }


def buscar_imoveis() -> Optional[Dict[str, Any]]:
    """
    Busca todos os imóveis da API Jetimob.
    
    Returns:
        Dicionário com os dados dos imóveis ou None em caso de erro
    """
    url = f"{API_BASE_URL}/{WEBSERVICE_KEY}/imoveis/todos"
    
    print("Buscando imóveis da API Jetimob...")
    
    # Usa timeout maior para leitura (a API pode demorar para retornar muitos dados)
    # Tupla: (connect_timeout, read_timeout)
    timeout = (10, REQUEST_TIMEOUT)
    
    resultado = fazer_requisicao(url=url, metodo="GET", timeout=timeout)
    
    if not resultado["success"]:
        print("\n❌ Erro ao buscar imóveis:")
        if "error" in resultado:
            print(f"   {resultado['error']}")
        else:
            print(f"   Status Code: {resultado.get('status_code')}")
            print(f"   Resposta: {resultado.get('data')}")
        return None
    
    return resultado["data"]


def salvar_imoveis_json(imoveis: Dict[str, Any], arquivo: str = DEFAULT_IMOVEIS_JSON) -> bool:
    """
    Salva os imóveis em um arquivo JSON, sobrescrevendo se já existir.
    
    Args:
        imoveis: Dados dos imóveis em formato de dicionário
        arquivo: Caminho do arquivo JSON para salvar
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        # Remove o arquivo se já existir
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"📄 Arquivo existente removido: {arquivo}")
        
        # Salva os novos dados
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(imoveis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Imóveis salvos com sucesso em: {arquivo}")
        
        # Mostra estatísticas básicas
        total = _contar_imoveis(imoveis)
        print(f"📊 Total de imóveis: {total}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {str(e)}")
        return False


def _contar_imoveis(imoveis: Dict[str, Any]) -> Union[int, str]:
    """
    Conta o total de imóveis na estrutura de dados.
    
    Args:
        imoveis: Dados dos imóveis
    
    Returns:
        Número total de imóveis ou "N/A" se não conseguir contar
    """
    if isinstance(imoveis, list):
        return len(imoveis)
    elif isinstance(imoveis, dict):
        # Tenta encontrar uma lista de imóveis no dicionário
        if "data" in imoveis and isinstance(imoveis["data"], list):
            return len(imoveis["data"])
        elif "imoveis" in imoveis and isinstance(imoveis["imoveis"], list):
            return len(imoveis["imoveis"])
    
    return "N/A"

