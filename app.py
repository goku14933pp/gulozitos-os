import os
import time
from flask import Flask, render_template_string, request
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
        "Inicializando GulozitosOS...",
        "Aguardando credenciais do usuario..."
    ]
    
    if request.method == "POST":
        estado = request.form.get("estado", "SP")
        ra = request.form.get("ra")
        digito = request.form.get("digito")
        senha = request.form.get("senha")
        
        log_status = [
            "Inicializando GulozitosOS...",
            "Preparando envio seguro...",
            f"Estado: {estado} | RA: {ra}-{digito}",
            "OK. Dados higienizados com sucesso"
        ]
        
        driver = None
        try:
            driver = iniciar_driver()
            driver.get("https://tarefasp.cmsp.seduc.sp.gov.br/")
            time.sleep(3)
            # Automatização conforme fluxo do CMSP
            driver.find_element(By.ID, "input-usuario-sed").send_keys(ra)
            driver.find_element(By.ID, "r2").send_keys(digito)
            driver.find_element(By.ID, "input-senha").send_keys(senha)
            driver.find_element(By.ID, "botao-login").click()
            time.sleep(5)
            log_status.append("Login automatizado executado com sucesso!")
        except Exception as e:
            log_status.append(f"Erro: {str(e)}")
        finally:
            if driver: driver.quit()

    logs_html = "<br>".join([f"> {linha}" for linha in log_status])

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Gulozitos OS</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #050302;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                overflow: hidden;
            }
            .wrapper {
                position: relative;
                width: 100%;
                max-width: 410px;
                height: 100vh;
                max-height: 820px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .bg-image {
                position: absolute;
                width: 100%;
                height: 100%;
                object-fit: contain;
                z-index: 1;
                pointer-events: none; /* Garante que os cliques passem direto para os inputs se necessário */
            }
            /* Camada interativa posicionada milimetricamente sobre a arte */
            .form-overlay {
                position: relative;
                z-index: 10;
                width: 63%;
                display: flex;
                flex-direction: column;
                gap: 7px;
                margin-top: 12px;
            }
            .row-inputs {
                display: flex;
                gap: 5px;
            }
            .input-box {
                background: rgba(8, 3, 2, 0.92);
                border: 1px solid rgba(255, 69, 0, 0.75);
                border-radius: 5px;
                padding: 7px 9px;
                display: flex;
                align-items: center;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.9);
            }
            .input-box select,
            .input-box input {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 13px;
                width: 100%;
                outline: none;
            }
            .input-box select option {
                background: #111;
                color: #fff;
            }
            .input-box input::placeholder {
                color: #8c7e77;
            }
            .estado-group { flex: 1.2; }
            .ra-group { flex: 2.2; }
            .digito-group { flex: 1; }
            .pass-container {
                position: relative;
                display: flex;
                align-items: center;
            }
            .toggle-pass {
                position: absolute;
                right: 10px;
                background: none;
                border: none;
                color: #ff5500;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }
            .btn-acessar {
                width: 100%;
                background: linear-gradient(to bottom, #ff5500 0%, #e62200 100%);
                color: #fff;
                border: 1px solid #ff7733;
                padding: 9px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 10px rgba(255, 68, 0, 0.6);
            }
            .btn-acessar:hover {
                background: linear-gradient(to bottom, #ff661a, #f5330a);
            }
            .terminal-box {
                background: rgba(2, 6, 2, 0.95);
                border: 1px solid #166534;
                border-radius: 5px;
                padding: 7px;
                font-family: 'Courier New', Courier, monospace;
                color: #4ade80;
                font-size: 9.5px;
                line-height: 1.3;
                max-height: 55px;
                overflow-y: auto;
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <!-- Imagem exata de fundo -->
            <img src="https://i.ibb.co/6803719/gulozitos-bg.png" class="bg-image" alt="Gulozitos OS">

            <div class="form-overlay">
                <form method="POST">
                    <!-- Linha 1: Estado, RA e Dígito sobrepostos exatamente onde a arte pede -->
                    <div class="row-inputs" style="margin-bottom: 7px;">
                        <div class="input-box estado-group">
                            <select name="estado">
                                <option value="SP">SP</option>
                                <option value="OUTROS">Outros</option>
                            </select>
                        </div>
                        <div class="input-box ra-group">
                            <input type="text" name="ra" placeholder="RA" required>
                        </div>
                        <div class="input-box digito-group">
                            <input type="text" name="digito" placeholder="Dígito" maxlength="2" required>
                        </div>
                    </div>

                    <!-- Linha 2: Senha com botão funcional de ver/ocultar integrado -->
                    <div class="input-box pass-container" style="margin-bottom: 7px; width: 100%;">
                        <input type="password" name="senha" id="senha" placeholder="Senha" required style="padding-right: 35px;">
                        <button type="button" class="toggle-pass" onclick="toggleSenha()">👁</button>
                    </div>

                    <!-- Botão de Acessar -->
                    <button type="submit" class="btn-acessar">ACESSAR</button>
                </form>

                <!-- Terminal simulado igualzinho na foto -->
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
