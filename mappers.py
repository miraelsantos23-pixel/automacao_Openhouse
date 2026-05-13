"""
Funções de mapeamento de dados
"""
from typing import Optional


def mapear_subtipo_para_value(subtipo: str) -> Optional[str]:
    """
    Mapeia o subtipo do imóvel para o value do option no select.
    
    Args:
        subtipo: Subtipo do imóvel (ex: "Apartamento")
    
    Returns:
        Value do option correspondente (ex: "APARTMENT") ou None
    """
    mapeamento = {
        "Apartamento": "APARTMENT",
        "Casa": "HOUSE",
        "Terreno": "LAND",
        "Sala Comercial": "COMMERCIAL_ROOM",
        "Loja": "STORE",
        "Cobertura": "PENTHOUSE",
        "Kitnet": "KITNET",
        "Sobrado": "TOWNHOUSE",
        "Chácara": "FARM",
        "Sítio": "FARM",
        "Fazenda": "FARM",
        "Galpão": "WAREHOUSE",
        "Prédio Comercial": "COMMERCIAL_BUILDING",
        "Casa de Condomínio": "CONDOMINIUM_HOUSE",
        "Flat": "FLAT",
        "Studio": "STUDIO",
    }
    
    return mapeamento.get(subtipo)

