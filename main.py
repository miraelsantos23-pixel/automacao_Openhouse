import os
import json
import time
import sys
import schedule
from datetime import datetime

# Identifica se estamos em ambiente Docker/VPS ou macOS
IS_VPS = os.environ.get("DOCKER_ENV") == "1"
IS_MAC = sys.platform == "darwin"

print("\n=== Automação Jetimob Iniciada ===")
print(f"Ambiente: {'VPS/Docker' if IS_VPS else 'Local'} | Sistema: {sys.platform}\n")

try:
    from api_client import buscar_imoveis, salvar_imoveis_json
    from jetimob_automation import automatizar_jetimob
    from config import DEFAULT_IMOVEIS_JSON, JETIMOB_PROGRESS_JSON
except Exception as err:
    print(f"\n❌ Erro nos imports iniciais: {err}")
    print("Verifique se todas as dependências estão instaladas (pip install -r requirements.txt).\n")
    if not IS_VPS:
        input("Pressione Enter para sair...")
    sys.exit(1)

def mostrar_mensagem(titulo, mensagem, tipo="info"):
    """Exibe mensagem via GUI se disponível, caso contrário apenas no console."""
    print(f"[{titulo}] {mensagem}")
    
    # Não exibe GUI em VPS ou se for restart automático
    if IS_VPS or "--restart" in sys.argv:
        return

    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        if tipo == "info":
            messagebox.showinfo(titulo, mensagem)
        elif tipo == "error":
            messagebox.showerror(titulo, mensagem)
        root.destroy()
    except Exception:
        # Silencioso se falhar GUI
        pass

def run_automation(is_restart=False):
    """Executa o ciclo completo da automação."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo de execução...")
    
    success = True
    if not is_restart:
        success = main_logic()
        
    if success:
        # Executa a automação. Headless=True é recomendado para VPS e estabilidade.
        automatizar_jetimob(headless=True)
    else:
        print("\n⚠️ Ciclo interrompido devido a falha na busca de dados.")

def main_logic():
    """Lógica de preparação de dados (API -> JSON)."""
    existe_imoveis = os.path.exists(DEFAULT_IMOVEIS_JSON)
    tem_conteudo = False
    
    if existe_imoveis:
        try:
            with open(DEFAULT_IMOVEIS_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list) and len(dados) > 0:
                    tem_conteudo = True
        except: pass

    if tem_conteudo:
        print(f"📂 Arquivo {DEFAULT_IMOVEIS_JSON} detectado. Preservando progresso.")
        return True

    print(f"🧹 Nova sessão: Limpando arquivos anteriores...")
    if existe_imoveis:
        try: os.remove(DEFAULT_IMOVEIS_JSON)
        except: pass

    try:
        with open(DEFAULT_IMOVEIS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f)
        
        with open(JETIMOB_PROGRESS_JSON, "w", encoding="utf-8") as f:
            json.dump({"processados": [], "index_atual": 0, "retry_count": 0, "skipped_due_to_error": False}, f, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao resetar arquivos: {e}")

    tentativas = 10
    for i in range(1, tentativas + 1):
        print(f"🔄 Buscando imóveis (Tentativa {i}/{tentativas})...")
        imoveis = buscar_imoveis()
        if imoveis is not None:
            salvar_imoveis_json(imoveis)
            return True
        if i < tentativas:
            time.sleep(3)
    
    mostrar_mensagem("Erro de Conexão", "Não foi possível conectar à API após 10 tentativas.", "error")
    return False

if __name__ == "__main__":
    is_restart = "--restart" in sys.argv
    # Se estiver em VPS ou o usuário passar o flag --vps, ativa o agendamento
    is_vps_mode = IS_VPS or "--vps" in sys.argv

    if not is_restart:
        mostrar_mensagem("Automação Jetimob", "A automação foi iniciada!\nO navegador trabalhará em segundo plano.")

    if is_vps_mode and not is_restart:
        print("🕒 MODO VPS ATIVO: A automação rodará todos os dias às 23:00 (GMT-3).")
        
        # Agenda para as 23:00
        schedule.every().day.at("23:00").do(run_automation)
        
        # Executa imediatamente a primeira vez (se quiser que rode só as 01:00, comente a linha abaixo)
        run_automation(is_restart=False)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Modo manual/local ou Restart de erro
        run_automation(is_restart=is_restart)
        
        if not is_restart and not IS_VPS:
            print("\n🏁 Execução finalizada.")
            input(">>> Pressione Enter para fechar...")
