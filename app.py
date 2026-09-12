import os
import time
import json
from flask import Flask, render_template_string, request
from PIL import Image

from google import genai
from google.genai import types

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    executable_path = "/usr/bin/chromedriver"
    if not os.path.exists(executable_path):
        executable_path = "chromedriver"
        
    service = Service(executable_path=executable_path)
    return webdriver.Chrome(service=service, options=options)

def analisar_questao_com_ia(screenshot_bytes, log_status):
    if not client:
        log_status.append("Erro: Chave GEMINI_KEY não configurada.")
        return None

    try:
        log_status.append("IA analisando estrutura da imagem...")
        image_part = types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
        
        prompt_instrucao = """
        Analise a imagem da questão da plataforma Sala do Futuro.
        Retorne estritamente em formato JSON válido com as seguintes chaves:
        {
          "tipo": "lacunas" | "multipla_escolha" | "verdadeiro_falso" | "dissertativa",
          "respostas_lacunas": ["palavra1", "palavra2"], 
          "opcao_correta": "texto exato da opção correta",
          "texto_dissertativo": "resposta redigida para questão aberta"
        }
        Retorne APENAS o JSON puro, sem blocos markdown.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt_instrucao]
        )
        
        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)
    except Exception as e:
        log_status.append(f"Erro na IA: {str(e)[:40]}")
        return None

def preencher_e_responder(driver, analise_ia, log_status):
    if not analise_ia:
        return False

    tipo = analise_ia.get("tipo")
    try:
        if tipo == "lacunas":
            respostas = analise_ia.get("respostas_lacunas", [])
            dropdowns = driver.find_elements(By.TAG_NAME, "select")
            for idx, select_elem in enumerate(dropdowns):
                if idx < len(respostas):
                    select_obj = Select(select_elem)
                    alvo = respostas[idx]
                    for option in select_obj.options:
                        if alvo.lower() in option.text.lower():
                            select_obj.select_by_visible_text(option.text)
                            break
            log_status.append("Lacunas preenchidas.")

        elif tipo in ["multipla_escolha", "verdadeiro_falso"]:
            opcao_texto = analise_ia.get("opcao_correta", "")
            if opcao_texto:
                elementos = driver.find_elements(By.XPATH, f"//*[contains(text(), '{opcao_texto}')]")
                for elem in elementos:
                    if elem.is_displayed():
                        driver.execute_script("arguments[0].click();", elem)
                        break
                log_status.append(f"Opção selecionada.")

        elif tipo == "dissertativa":
            texto = analise_ia.get("texto_dissertativo", "")
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            if textareas:
                textareas[0].clear()
                textareas[0].send_keys(texto)
                log_status.append("Texto inserido.")

        time.sleep(1)
        botoes = driver.find_elements(By.XPATH, "//button[contains(text(), 'Responder') or contains(text(), 'Enviar') or contains(text(), 'Avançar') or contains(text(), 'Próxima')]")
        if botoes:
            driver.execute_script("arguments[0].click();", botoes[0])
            log_status.append("Avançando...")

        return True
    except Exception as e:
        log_status.append(f"Erro no preenchimento: {str(e)[:30]}")
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    log_status = ["GulozitosOS inicializado.", "Aguardando credenciais..."]
    
    if request.method == "POST":
        ra_completo = request.form.get("ra_completo", "").strip()
        senha = request.form.get("senha", "").strip()
        acao = request.form.get("acao", "pendentes")
        
        log_status = [f"Modo: {acao.capitalize()}", f"Autenticando RA: {ra_completo}", "Iniciando navegador..."]
        
        driver = None
        try:
            driver = iniciar_driver()
            driver.get("https://saladofuturo.educacao.sp.gov.br/login-alunos")
            time.sleep(3)
            
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if len(inputs) >= 2:
                inputs[0].send_keys(ra_completo)
                inputs[1].send_keys(senha)
                
                botoes_login = driver.find_elements(By.XPATH, "//button[@type='submit' or contains(text(), 'Entrar')]")
                if botoes_login:
                    botoes_login[0].click()
                    time.sleep(5)
            
            log_status.append("Navegando para as tarefas...")
            if acao == "expiradas":
                links = driver.find_elements(By.XPATH, "//*[contains(text(), 'Expiradas')]")
            else:
                links = driver.find_elements(By.XPATH, "//*[contains(text(), 'Pendentes')]")
                
            if links:
                driver.execute_script("arguments[0].click();", links[0])
                time.sleep(3)

            cards = driver.find_elements(By.CSS_SELECTOR, ".card-tarefa, .task-item, [role='button']")
            if cards:
                driver.execute_script("arguments[0].click();", cards[0])
                time.sleep(4)
                
                for q in range(1, 10):
                    log_status.append(f"Processando Questão {q}...")
                    screenshot = driver.get_screenshot_as_png()
                    analise = analisar_questao_com_ia(screenshot, log_status)
                    preencher_e_responder(driver, analise, log_status)
                    time.sleep(3)
            else:
                log_status.append("Nenhuma atividade encontrada.")

        except Exception as e:
            log_status.append(f"Aviso: {str(e)[:40]}")
        finally:
            if driver:
                try: driver.quit()
                except: pass

    logs_html = "<br>".join([f"> {linha}" for linha in log_status])

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gulozitos - Sala do Futuro</title>
        <style>
            body { margin: 0; background-color: #070913; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: #fff; }
            .container { width: 100%; max-width: 420px; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            .header { text-align: center; margin-bottom: 25px; }
            .header h1 { font-size: 34px; background: linear-gradient(135deg, #ff7a00, #ffb347); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
            .card { background: rgba(18, 22, 38, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; width: 100%; }
            .input-group { margin-bottom: 18px; }
            .input-group label { display: block; font-size: 13px; color: #c5cee0; margin-bottom: 8px; }
            .input-wrapper { background: rgba(10, 13, 24, 0.85); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; padding: 12px; display: flex; }
            .input-wrapper input { background: transparent; border: none; color: #fff; width: 100%; outline: none; }
            .btn-action { width: 100%; background: rgba(28, 33, 53, 0.95); border: 1px solid rgba(255,255,255,0.14); color: #fff; padding: 14px; border-radius: 10px; cursor: pointer; margin-bottom: 12px; }
            .terminal-box { background: rgba(4, 6, 12, 0.95); border: 1px solid #104523; border-radius: 8px; padding: 12px; font-family: monospace; color: #4ade80; font-size: 11px; max-height: 120px; overflow-y: auto; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Gulozitos</h1><p>para sala do futuro e cmsp!</p></div>
            <div class="card">
                <form method="POST">
                    <div class="input-group"><label>RA</label><div class="input-wrapper"><input type="text" name="ra_completo" placeholder="RA + dígito + sp" required></div></div>
                    <div class="input-group"><label>Senha</label><div class="input-wrapper"><input type="password" name="senha" placeholder="Senha" required></div></div>
                    <button type="submit" name="acao" value="pendentes" class="btn-action">Atividades Pendentes</button>
                    <button type="submit" name="acao" value="expiradas" class="btn-action">Atividades Expiradas</button>
                </form>
                <div class="terminal-box">{{ logs_html | safe }}</div>
            </div>
        </div>
    </body>
    </html>
    """, logs_html=logs_html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
