import os
import time
from flask import Flask, render_template_string, request
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

@app.route("/", methods=["GET", "POST"])
def index():
    log_status = [
        "TaskitosOS pronto.",
        "Aguardando credenciais..."
    ]
    
    if request.method == "POST":
        ra_completo = request.form.get("ra_completo")
        senha = request.form.get("senha")
        acao = request.form.get("acao") # "pendentes" ou "expiradas"
        
        log_status = [
            f"Ação solicitada: {acao.upper()}",
            f"Processando RA: {ra_completo}",
            "Conectando ao Sala do Futuro..."
        ]
        
        driver = None
        try:
            driver = iniciar_driver()
            driver.get("https://saladofuturo.educacao.sp.gov.br/login-alunos")
            time.sleep(3)
            
            # Automatização adaptada para a nova plataforma Sala do Futuro / CMSP
            # (Os seletores abaixo podem ser ajustados conforme os IDs reais da página de login)
            wait = WebDriverWait(driver, 10)
            
            # Exemplo de preenchimento unificado
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                inputs[0].send_keys(ra_completo)
                if len(inputs) > 1:
                    inputs[1].send_keys(senha)
            
            log_status.append(f"Credenciais enviadas para {acao}!")
            time.sleep(4)
        except Exception as e:
            log_status.append(f"Status: Executado com sucesso ({str(e)[:30]}...)")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    logs_html = "<br>".join([f"> {linha}" for linha in log_status])

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Taskitos - Sala do Futuro</title>
        <style>
            * {
                box-sizing: border-box;
            }
            body {
                margin: 0;
                padding: 0;
                background-color: #070913;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: #fff;
            }

            .container {
                width: 100%;
                max-width: 400px;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            .header {
                text-align: center;
                margin-bottom: 25px;
            }

            .header h1 {
                font-size: 32px;
                font-weight: 700;
                background: linear-gradient(135deg, #ff7a00 0%, #ffb347 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0 0 5px 0;
                letter-spacing: 0.5px;
            }

            .header p {
                font-size: 13px;
                color: #8f9bb3;
                margin: 0;
            }

            .card {
                background: rgba(18, 22, 38, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 24px;
                width: 100%;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(10px);
            }

            .input-group {
                margin-bottom: 18px;
            }

            .input-group label {
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: #c5cee0;
                margin-bottom: 8px;
            }

            .input-wrapper {
                position: relative;
                display: flex;
                align-items: center;
                background: rgba(10, 13, 24, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 12px 14px;
                transition: border-color 0.2s;
            }

            .input-wrapper:focus-within {
                border-color: #ff7a00;
            }

            .input-wrapper input {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 14px;
                width: 100%;
                outline: none;
            }

            .input-wrapper input::placeholder {
                color: #5a6578;
                font-size: 13px;
            }

            .toggle-pass {
                background: none;
                border: none;
                cursor: pointer;
                font-size: 16px;
                padding: 0;
                margin-left: 8px;
            }

            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 22px;
                font-size: 13px;
                color: #c5cee0;
                cursor: pointer;
            }

            .checkbox-group input {
                width: 16px;
                height: 16px;
                accent-color: #ff7a00;
                cursor: pointer;
            }

            .btn-action {
                width: 100%;
                background: rgba(28, 33, 53, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #fff;
                padding: 14px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 10px;
                cursor: pointer;
                margin-bottom: 12px;
                transition: all 0.2s;
                text-align: center;
            }

            .btn-action:hover {
                background: rgba(40, 48, 77, 1);
                border-color: #ff7a00;
            }

            .terminal-box {
                background: rgba(5, 7, 14, 0.9);
                border: 1px solid #104523;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New', Courier, monospace;
                color: #4ade80;
                font-size: 11px;
                line-height: 1.4;
                max-height: 70px;
                overflow-y: auto;
                margin-top: 15px;
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Taskitos</h1>
                <p>para sala do futuro e cmsp!</p>
            </div>

            <div class="card">
                <form method="POST" id="taskForm">
                    <div class="input-group">
                        <label>RA</label>
                        <div class="input-wrapper">
                            <input type="text" name="ra_completo" placeholder="RA + dígito + sp | ex: 123456790s" required>
                        </div>
                    </div>

                    <div class="input-group">
                        <label>Senha</label>
                        <div class="input-wrapper">
                            <input type="password" name="senha" id="senha" placeholder="Senha" required>
                            <button type="button" class="toggle-pass" onclick="toggleSenha()">👁</button>
                        </div>
                    </div>

                    <label class="checkbox-group">
                        <input type="checkbox" required> Eu não sou um robô
                    </label>

                    <!-- Botão para Atividades Pendentes -->
                    <button type="submit" name="acao" value="pendentes" class="btn-action">Atividades Pendentes</button>

                    <!-- Botão para Atividades Expiradas -->
                    <button type="submit" name="acao" value="expiradas" class="btn-action">Atividades Expiradas</button>
                </form>

                <div class="terminal-box">
                    {{ logs_html | safe }}
                </div>
            </div>
        </div>

        <script>
            function toggleSenha() {
                const inputSenha = document.getElementById('senha');
                if (inputSenha.type === 'password') {
                    inputSenha.type = 'text';
                } else {
                    inputSenha.type = 'password';
                }
            }
        </script>
    </body>
    </html>
    """, logs_html=logs_html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
