import sys
import traceback
from jetimob_automation import carregar_imoveis_json, criar_driver_firefox, processar_imovel_jetimob

TEST_LIMIT = 3

def main():
    print(f"Iniciando teste automatizado Jetimob (processando {TEST_LIMIT} imóveis)...")
    try:
        imoveis = carregar_imoveis_json()[:TEST_LIMIT]
        driver = criar_driver_firefox(headless=False)  # Tira headless para testar rendering UI real
        sucesso = []
        for idx, imovel in enumerate(imoveis, 1):
            try:
                ok = processar_imovel_jetimob(driver, imovel, idx, len(imoveis))
                sucesso.append(ok)
            except Exception as e:
                print(f"Exceção ao processar imóvel {idx}: {e}")
                traceback.print_exc()
                sucesso.append(False)
        driver.quit()
        print(f"\nResultados por imóvel: {sucesso}")
        print(f"Todos processados: {'✅' if all(sucesso) else '⚠️'}\n")
    except Exception as e:
        print(f"Erro geral no teste: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
