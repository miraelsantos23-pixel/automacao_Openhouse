import sys
import json
import os
import logging

# Configura logger para nível INFO para evitar poluição no console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Garante que todos arquivos serão lidos/gravar a partir do mesmo diretório do .exe
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
import random
import re
import string
import time
from datetime import datetime
from typing import Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import (
    JETIMOB_URL,
    DEFAULT_IMOVEIS_JSON,
    JETIMOB_ERROS_JSON,
    JETIMOB_PROGRESS_JSON,
    JETIMOB_REPORT_TXT,
    PAGE_LOAD_DELAY,
    ELEMENT_WAIT_TIMEOUT,
    ACTION_DELAY,
    BETWEEN_IMOVEIS_DELAY,
    JETIMOB_EMAIL,
    JETIMOB_PASSWORD
)

def limpar_arquivo_erros(arquivo_erros: str = JETIMOB_ERROS_JSON) -> None:
    with open(arquivo_erros, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print(f"🧹 Arquivo de erros limpo: {arquivo_erros}")

def carregar_imoveis_json(arquivo_json: str = DEFAULT_IMOVEIS_JSON) -> list[dict]:
    if not os.path.exists(arquivo_json):
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_json}")
    print(f"📂 Carregando imóveis de {arquivo_json}...")
    with open(arquivo_json, "r", encoding="utf-8") as f:
        imoveis = json.load(f)
    if not isinstance(imoveis, list):
        raise ValueError("O arquivo JSON deve conter uma lista de imóveis")
    print(f"✅ {len(imoveis)} imóveis carregados")
    return imoveis

def checkpoint_handler(action: str, dados=None):
    if action == "save":
        with open(JETIMOB_PROGRESS_JSON, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return dados
    elif action == "load":
        if os.path.exists(JETIMOB_PROGRESS_JSON):
            try:
                with open(JETIMOB_PROGRESS_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Garante campos necessários
                    if "processados" not in data: data["processados"] = []
                    if "retry_count" not in data: data["retry_count"] = 0
                    if "skipped_due_to_error" not in data: data["skipped_due_to_error"] = False
                    return data
            except:
                pass
        return {"processados": [], "index_atual": 0, "retry_count": 0, "skipped_due_to_error": False}

def gerar_relatorio(total_sucesso, total_erros, total_nao_encontrados, totais, tempo_inicio):
    tempo_total = (datetime.now() - tempo_inicio).total_seconds()
    with open(JETIMOB_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("=== RELATÓRIO DE EXECUÇÃO JETIMOB ===\n")
        f.write(f"Data final: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tempo total: {tempo_total:.2f}s\n")
        f.write(f"Total executado nesta sessão: {totais}\n")
        f.write(f"Sucessos: {total_sucesso}\n")
        f.write(f"Erros/Falhas: {total_erros}\n")
        f.write(f"Não encontrados (skip): {total_nao_encontrados}\n")
    print(f"📊 Relatório gerado em {JETIMOB_REPORT_TXT}")

def criar_driver_firefox(headless: bool = False) -> webdriver.Firefox:
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("--headless")
    
    # Configurações de perfil para evitar detecção e melhorar estabilidade
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json")
    
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(60)
        try:
            driver.maximize_window()
        except Exception:
            # Em modo headless ou alguns ambientes Linux, maximize pode falhar
            driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        print(f"❌ Erro ao iniciar Firefox: {e}")
        print("\n💡 DICA PARA MAC/LINUX:")
        print("Certifique-se de que o 'geckodriver' está instalado e no PATH.")
        print("No Mac: 'brew install geckodriver'")
        print("No Linux: Instalado automaticamente via Docker ou 'apt install firefox-geckodriver'")
        raise e

def salvar_imovel_erro(imovel: dict, arquivo_erros: str = JETIMOB_ERROS_JSON) -> None:
    if os.path.exists(arquivo_erros):
        try:
            with open(arquivo_erros, "r", encoding="utf-8") as f:
                erros = json.load(f)
            if not isinstance(erros, list):
                erros = []
        except Exception:
            erros = []
    else:
        erros = []
    codigo = imovel.get("codigo")
    if not any(e.get("codigo") == codigo for e in erros):
        erros.append(imovel)
        with open(arquivo_erros, "w", encoding="utf-8") as f:
            json.dump(erros, f, ensure_ascii=False, indent=2)
        print(f"   📝 Imóvel com erro salvo para retry: código={codigo}")

def carregar_imoveis_erro(arquivo_erros: str = JETIMOB_ERROS_JSON) -> list[dict]:
    if not os.path.exists(arquivo_erros):
        return []
    try:
        with open(arquivo_erros, "r", encoding="utf-8") as f:
            erros = json.load(f)
        if not isinstance(erros, list):
            return []
        return erros
    except Exception:
        return []

def processar_imovel_jetimob(driver: webdriver.Firefox, imovel: dict, index: int, total: int, verificar_login: bool = True) -> bool:
    logging.info(f"Iniciando processamento de imóvel {index}/{total} | código={imovel.get('codigo')}")
    codigo = imovel.get("codigo")
    print(f"\n{'='*60}")
    print(f"🏠 Jetimob - Processando imóvel {index}/{total} | código={codigo}")
    print(f"{'='*60}")
    try:
        driver.get(JETIMOB_URL)
        time.sleep(PAGE_LOAD_DELAY)
        if verificar_login:
            if is_jetimob_login_page(driver):
                print("ℹ️  Página de login detectada (Jetimob)")
                if not preencher_formulario_login(driver):
                    print("❌ Erro ao realizar login; interrompendo para evitar bloqueios.")
                    return False
                time.sleep(PAGE_LOAD_DELAY)
                driver.get(JETIMOB_URL)
                time.sleep(PAGE_LOAD_DELAY)
        # Buscar imóvel por código - seletores resilientes
        css_busca_codigo = "input[placeholder*='código'], input[placeholder*='codigo'], input[name*='codigo'], input#codigo, input[type='text']"
        if not preencher_input_por_css(driver, css_busca_codigo, codigo, "Código (busca)"):
            print("❌ Não foi possível preencher o código na busca.")
            registrar_codigo_nao_encontrado(codigo)
            return False
        time.sleep(ACTION_DELAY)
        # Melhores Práticas: Busca do botão "Filtrar" por correspondência de texto para isolar o clique exato de busca e filtro de código
        xpath_filtrar = "//*[contains(translate(text(), 'FILTRAR', 'filtrar'), 'filtrar') or contains(translate(@value, 'FILTRAR', 'filtrar'), 'filtrar') or contains(translate(@title, 'FILTRAR', 'filtrar'), 'filtrar') or contains(translate(@aria-label, 'FILTRAR', 'filtrar'), 'filtrar')]"
        if not clicar_por_xpath(driver, xpath_filtrar, "Botão Filtrar (Busca)"):
            print("❌ Não foi possível clicar no botão 'Filtrar'.")
            # Retorna sinal específico para disparar lógica de restart/retry
            return "TIMEOUT_FILTRAR"
        time.sleep(PAGE_LOAD_DELAY)

        # Busca o botão da seta para abrir a ficha do imóvel específico renderizado pela tabela/listagem
        xpath_selecionar_imovel = f"//a[contains(@href, '{codigo}') and contains(@class, 'button-open')] | //a[@title='Ver ficha'] | //a[contains(@class, 'button-open')]"
        if not clicar_por_xpath(driver, xpath_selecionar_imovel, f"Seta 'Ver ficha' ({codigo})"):
            print(f"❌ Não foi possível clicar/entrar nos detalhes do imóvel {codigo}. Talvez não listado.")
            registrar_codigo_nao_encontrado(codigo)
            return False
            
        time.sleep(PAGE_LOAD_DELAY)

        # Melhores práticas em Selenium: Encontra posições exatas por match de texto Case Insensitive renderizado ou em atributos de acessibilidade
        xpath_editar = "//*[contains(translate(text(), 'EDITAR', 'editar'), 'editar') or contains(translate(@title, 'EDITAR', 'editar'), 'editar') or contains(translate(@aria-label, 'EDITAR', 'editar'), 'editar')]"
        if not clicar_por_xpath(driver, xpath_editar, "Botão Editar (XPath Text)"):
            print("❌ Não foi possível clicar no botão de editar usando XPath de texto.")
            registrar_codigo_nao_encontrado(codigo)
            return False
        time.sleep(PAGE_LOAD_DELAY)
        css_input_codigo = "input[placeholder='Informe o código']"
        try:
            input_el = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_input_codigo))
            )
            # Ler o valor preexistente no input para alimentar a lógica de timestamp avançado
            codigo_na_pagina = driver.execute_script("return arguments[0].value;", input_el) or codigo
        except Exception:
            codigo_na_pagina = codigo
            
        novo_codigo = _gerar_codigo_com_timestamp(codigo_na_pagina)

        if not preencher_input_por_css(driver, css_input_codigo, novo_codigo, "Novo código (timestamp)"):
            print("❌ Não foi possível preencher o novo código.")
            return False
        time.sleep(ACTION_DELAY)
        
        # Botão salvar especificado pelo cliente (a#step-11-next-button)
        xpath_salvar = "//*[@id='step-11-next-button'] | //a[contains(translate(text(), 'SALVAR', 'salvar'), 'salvar')]"
        if not clicar_por_xpath(driver, xpath_salvar, "Botão Salvar"):
            print("❌ Não foi possível clicar no botão 'Salvar'.")
            return False

        print(f"✅ Jetimob - Imóvel {index} processado com sucesso!")
        logging.info(f"Imóvel {index} (código={codigo}) processado com SUCESSO.")
        return True
    except Exception as e:
        print(f"❌ Erro inesperado ao processar imóvel {index} (código={codigo}): {e}")
        logging.error(f"Erro ao processar imóvel {index} (código={codigo}): {e}")
        return False

def is_jetimob_login_page(driver) -> bool:
    """Verifica se a página atual é a de login da Jetimob."""
    try:
        # Exemplos: busca label/email ou botão login
        WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input#email, input[name*='mail']"))
        )
        WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input#password, input[name*='senha']"))
        )
        WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button, input[type='submit']"))
        )
        return True
    except Exception:
        return False

def preencher_formulario_login(driver) -> bool:
    """Tenta preencher o formulário de login da Jetimob."""
    try:
        # Flexibilidade para diferentes páginas/estruturas
        email_selectors = ["input[type='email']", "input#email", "input[name*='mail']"]
        senha_selectors = ["input[type='password']", "input#password", "input[name*='senha']"]
        button_selectors = ["button[type='submit']", "button", "input[type='submit']"]
        email_foi_preenchido = False
        for sel in email_selectors:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for idx, campo in enumerate(elems):
                try:
                    if not campo.is_displayed() or not campo.is_enabled():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                    driver.execute_script("arguments[0].focus();", campo)
                    try:
                        campo.click()
                        campo.clear()
                        campo.send_keys(JETIMOB_EMAIL)
                    except Exception:
                        driver.execute_script(f"arguments[0].value='{JETIMOB_EMAIL}';", campo)
                    email_foi_preenchido = True
                    break
                except Exception:
                    continue
            if email_foi_preenchido:
                break
        senha_foi_preenchida = False
        for sel in senha_selectors:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for idx, campo in enumerate(elems):
                try:
                    if not campo.is_displayed() or not campo.is_enabled():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                    driver.execute_script("arguments[0].focus();", campo)
                    try:
                        campo.click()
                        campo.clear()
                        campo.send_keys(JETIMOB_PASSWORD)
                    except Exception:
                        driver.execute_script(f"arguments[0].value='{JETIMOB_PASSWORD}';", campo)
                    senha_foi_preenchida = True
                    break
                except Exception:
                    continue
            if senha_foi_preenchida:
                break
        for sel in button_selectors:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                elems[0].click()
                print("🔐 Login Jetimob enviado.")
                return True
        print("❌ Não encontrou botão de login Jetimob.")
        return False
    except Exception as e:
        print(f"❌ Falha inesperada no login Jetimob: {e}")
        return False

def preencher_input_por_css(driver, selector, valor, contexto=None) -> bool:
    """Tenta preencher um campo de input localizado por CSS."""
    try:
        campo = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
            time.sleep(0.5)
            campo.send_keys(Keys.CONTROL + "a")
            campo.send_keys(Keys.DELETE)
            time.sleep(0.2)
            campo.send_keys(str(valor))
            return True
        except Exception:
            driver.execute_script(f"arguments[0].value='{valor}';", campo)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", campo)
            return True
    except TimeoutException:
        print(f"⏳ Timeout ao localizar input '{selector}'")
        return False
    except Exception as e:
        print(f"❌ Erro ao preencher input '{selector}': {e}")
        return False

def clicar_por_css(driver, selector, contexto=None) -> bool:
    """Tenta clicar em um elemento localizado por CSS Selector. Tenta fechar overlays/modais que possam bloquear o clique."""
    def fechar_overlays_se_existentes():
        overlays_selectors = [
            '.modal', '.modal-overlay', '.overlay', '.question-text', '.cookie-consent', '.jet-modal',
            'div[role="dialog"]', 'div[aria-modal="true"]'
        ]
        algum_overlay = False
        for sel in overlays_selectors:
            overlays = driver.find_elements(By.CSS_SELECTOR, sel)
            if overlays:
                for ov in overlays:
                    if ov.is_displayed():
                        try:
                            driver.execute_script("arguments[0].style.visibility='hidden'; arguments[0].style.display='none';", ov)
                            algum_overlay = True
                        except Exception:
                            pass
        return algum_overlay

    try:
        botao = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        try:
            botao.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", botao)
            except Exception as e3:
                print(f"❌ Erro ao tentar click JS também: {e3}")
                return False
        return True
    except TimeoutException:
        print(f"⏳ Timeout ao localizar/clicar '{selector}' ({contexto})")
        return False
    except Exception as e:
        print(f"❌ Erro ao clicar '{selector}' ({contexto}): {e}")
        return False

def clicar_por_xpath(driver, selector, contexto=None) -> bool:
    """Tenta clicar em um elemento localizado por XPath reproduzindo a resiliencia contra overlays."""
    def fechar_overlays_se_existentes():
        overlays_selectors = ['.modal', '.modal-overlay', '.overlay', '.question-text', '.cookie-consent', '.jet-modal', 'div[role="dialog"]', 'div[aria-modal="true"]']
        algum_overlay = False
        for sel in overlays_selectors:
            overlays = driver.find_elements(By.CSS_SELECTOR, sel)
            for ov in overlays:
                if ov.is_displayed():
                    try:
                        driver.execute_script("arguments[0].style.visibility='hidden'; arguments[0].style.display='none';", ov)
                        algum_overlay = True
                    except Exception: pass
        return algum_overlay

    try:
        botao = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, selector)))
        try:
            botao.click()
        except Exception:
            if fechar_overlays_se_existentes(): time.sleep(0.5)
            try:
                botao.click()
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", botao)
                except Exception as e3:
                    print(f"❌ Erro ao tentar click JS também (XPath): {e3}")
                    return False
        return True
    except TimeoutException:
        print(f"⏳ Timeout ao localizar/clicar XPath '{selector}' ({contexto})")
        return False
    except Exception as e:
        print(f"❌ Erro ao clicar XPath '{selector}' ({contexto}): {e}")
        return False


def _gerar_codigo_com_timestamp(codigo_original: str, now: datetime | None = None) -> str:
    """
    Gera código no novo formato: 2 letras + 5 chars identificador único + ddmmyy
    Se o código já estiver no novo formato, mantém o identificador único e atualiza apenas a data.
    Se estiver no formato antigo, converte para o novo formato gerando identificador único.
    """
    if now is None:
        now = datetime.now()

    codigo_original = str(codigo_original or "")

    # Verifica se já está no novo formato: exatamente 13 chars
    # Formato: 2 letras maiúsculas + 5 alfanuméricos + 6 dígitos (ddmmyy)
    if len(codigo_original) == 13:
        primeiros_2 = codigo_original[:2]
        identificador_5 = codigo_original[2:7]
        data_str = codigo_original[7:]

        if (primeiros_2.isupper() and primeiros_2.isalpha() and
            all(c.isalnum() for c in identificador_5) and
            data_str.isdigit() and len(data_str) == 6):
            # Já está no novo formato: mantém identificador único (7 primeiros chars) e atualiza data
            identificador_unico = codigo_original[:7]
            data_atual = now.strftime("%d%m%y")
            return f"{identificador_unico}{data_atual}"

    # Formato antigo ou inválido: converte para novo formato
    apenas_letras = re.sub(r"[^a-zA-Z]", "", codigo_original)
    letras_iniciais = (apenas_letras[:2] if len(apenas_letras) >= 2 else "XX").upper()

    chars_possiveis = string.ascii_letters.upper() + string.digits
    identificador_unico = ''.join(random.choices(chars_possiveis, k=5))

    data_atual = now.strftime("%d%m%y")
    return f"{letras_iniciais}{identificador_unico}{data_atual}"

def registrar_codigo_nao_encontrado(codigo, arquivo_txt="imoveis_nao_encontrados.txt"):
    """Registra código (único) de imóvel não encontrado no arquivo .txt."""
    try:
        if not os.path.exists(arquivo_txt):
            with open(arquivo_txt, "w", encoding="utf-8") as f:
                f.write("")
        with open(arquivo_txt, "r+", encoding="utf-8") as f:
            linhas = set(l.strip() for l in f if l.strip())
            if str(codigo) not in linhas:
                f.write(str(codigo) + "\n")
                print(f"[INFO] Código não encontrado registrado ({codigo}) em {arquivo_txt}")
    except Exception as e:
        print(f"[WARN] Falha ao registrar código não encontrado ({codigo}): {e}")

def automatizar_jetimob(headless=True):
    """
    Função principal da automação Jetimob. Executa o fluxo para editar imóveis no Jetimob.
    Mostra alerta, faz login, processa todos os imóveis não processados.
    """
    logging.info("=== AUTOMAÇÃO JETIMOB INICIADA ===")
    print("\n🚀 [ALERTA] Automação Jetimob iniciada! Todas as operações subsequentes serão registradas no console e nos relatórios.")
    
    tempo_inicio = datetime.now()
    checkpoint = checkpoint_handler("load")
    processados = checkpoint.get("processados", [])
    
    driver = None
    try:
        driver = criar_driver_firefox(headless=headless)
        print("\n🌐 Navegador Selenium iniciado.")
        
        # NAVEGAR E FAZER LOGIN ANTES DO LOOP
        print("\n🔐 Navegando para Jetimob e realizando login...")
        driver.get(JETIMOB_URL)
        time.sleep(PAGE_LOAD_DELAY)
        if is_jetimob_login_page(driver):
            print("ℹ️  Página de login detectada.")
            if not preencher_formulario_login(driver):
                print("❌ Falha ao logar no Jetimob. Abortando.")
                return
            time.sleep(PAGE_LOAD_DELAY)
            driver.get(JETIMOB_URL)
            time.sleep(PAGE_LOAD_DELAY)
            print("✅ Login realizado com sucesso!")
        else:
            print("ℹ️  Já estava logado ou página de login não detectada.")
        
        imoveis = carregar_imoveis_json()
        print(f"\n🔢 Carregado {len(imoveis)} imóveis do arquivo.")
        
        # Filtrar os que AINDA NÃO FORAM PROCESSADOS
        nao_processados = [i for i in imoveis if str(i.get("codigo")) not in processados]
        subset = nao_processados
        
        if not subset:
            print("✅ Todos os imóveis já foram processados! Nada a fazer.")
            return

        sucessos = 0
        erros = 0
        total_global = len(imoveis)
        ja_processados_count = len(processados)

        for idx, imovel in enumerate(subset, 1):
            codigo_str = str(imovel.get("codigo", ""))
            progresso_global = ja_processados_count + idx
            print(f"\n➡️ Processando imóvel {progresso_global}/{total_global} | Código: {codigo_str}")
            if processados:
                print(f"✅ Último código processado com sucesso: {processados[-1]}")
            
            resultado = processar_imovel_jetimob(driver, imovel, idx, len(subset), verificar_login=False)
            
            if resultado is True:
                sucessos += 1
                checkpoint["processados"].append(codigo_str)
                checkpoint["retry_count"] = 0
                checkpoint["skipped_due_to_error"] = False
                checkpoint_handler("save", checkpoint)
            elif resultado == "TIMEOUT_FILTRAR":
                retry_count = checkpoint.get("retry_count", 0)
                skipped = checkpoint.get("skipped_due_to_error", False)
                
                if not skipped:
                    if retry_count < 5:
                        checkpoint["retry_count"] = retry_count + 1
                        checkpoint_handler("save", checkpoint)
                        print(f"\n⚠️ Timeout no botão Filtrar. Reiniciando aplicação em 5s... (Tentativa {checkpoint['retry_count']}/5 para o código {codigo_str})")
                        time.sleep(5)
                        try:
                            if driver: driver.quit()
                        except: pass
                        
                        args = [sys.executable]
                        if not getattr(sys, 'frozen', False):
                            args.append('main.py')
                        args.append('--restart')
                        os.execv(sys.executable, args)
                    else:
                        checkpoint["retry_count"] = 0
                        checkpoint["processados"].append(codigo_str)
                        checkpoint["skipped_due_to_error"] = True
                        checkpoint_handler("save", checkpoint)
                        print(f"\n⚠️ Falha persistente (5x) no código {codigo_str}. Pulando para o próximo e reiniciando em 5s...")
                        time.sleep(5)
                        try:
                            if driver: driver.quit()
                        except: pass
                        
                        args = [sys.executable]
                        if not getattr(sys, 'frozen', False):
                            args.append('main.py')
                        args.append('--restart')
                        os.execv(sys.executable, args)
                else:
                    print(f"\n❌ Erro persistente mesmo após pular código. Encerrando e registrando erro fatal.")
                    try:
                        screenshot_path = os.path.abspath("erro_fatal_screenshot.png")
                        driver.save_screenshot(screenshot_path)
                        with open("erro_fatal_log.txt", "w", encoding="utf-8") as f:
                            f.write(f"ERRO FATAL: Timeout persistente no botão Filtrar ou Erro de Janela.\n")
                            f.write(f"Código atual: {codigo_str}\n")
                            f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Screenshot salva em: {screenshot_path}\n")
                        print(f"📸 Screenshot salva em: {screenshot_path}")
                        print(f"📄 Log de erro fatal gerado em: erro_fatal_log.txt")
                    except Exception as e_scr:
                        print(f"⚠️ Não foi possível salvar screenshot ou log: {e_scr}")
                    try:
                        if driver: driver.quit()
                    except: pass
                    sys.exit(1)
            else:
                erros += 1
                salvar_imovel_erro(imovel)
                checkpoint["processados"].append(codigo_str)
                checkpoint["retry_count"] = 0
                checkpoint["skipped_due_to_error"] = False
                checkpoint_handler("save", checkpoint)

            if idx < len(subset):
                print(f"\n⏳ Aguardando {BETWEEN_IMOVEIS_DELAY}s antes do próximo imóvel...")
                time.sleep(BETWEEN_IMOVEIS_DELAY)
                
        # Gera relatório final do lote
        gerar_relatorio(sucessos, erros, 0, len(subset), tempo_inicio)

        print("\n🏁 Automação concluída com sucesso!")
    except Exception as e:
        err_msg = str(e)
        # Detecta o erro de timeout de rede ou contexto descartado (janela fechada)
        if any(msg in err_msg for msg in ["netTimeout", "Reached error page", "10060", "discarded", "NoSuchWindow"]):
            print(f"\n⚠️ Erro de rede ou contexto detectado: {err_msg}")
            
            retry_count = checkpoint.get("retry_count", 0)
            if retry_count < 5:
                checkpoint["retry_count"] = retry_count + 1
                checkpoint_handler("save", checkpoint)
                print(f"⏳ Reiniciando aplicação em 5 segundos... (Tentativa {checkpoint['retry_count']}/5)")
                time.sleep(5)
                try:
                    if driver: driver.quit()
                except: pass
                
                args = [sys.executable]
                if not getattr(sys, 'frozen', False):
                    args.append('main.py')
                args.append('--restart')
                os.execv(sys.executable, args)
            else:
                # Se já tentou 5 vezes o mesmo ponto, tentamos pular o atual se houver um código sendo processado
                print(f"❌ Falha persistente após 5 tentativas. Encerrando.")
                try:
                    screenshot_path = os.path.abspath("erro_fatal_screenshot.png")
                    if driver:
                        driver.save_screenshot(screenshot_path)
                        print(f"📸 Screenshot salva em: {screenshot_path}")
                except: pass
                sys.exit(1)

        print(f"\n❌ ERRO FATAL NO FLUXO: {e}")
        import traceback; traceback.print_exc()
    finally:
        print("\n" + "="*60)
        print("🏁 PROCESSO FINALIZADO")
        print("="*60)
        try:
            if driver:
                driver.quit()
                print("\n🦊 Driver Selenium encerrado.")
                logging.info("Driver Selenium encerrado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao fechar driver Selenium: {e}")
# Certifique-se de que todas as funções auxiliares usadas (preencher_input_por_css, clicar_por_css, etc.) também estejam incluídas!
