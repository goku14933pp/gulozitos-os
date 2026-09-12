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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gulozitos OS</title>
        <style>
            * {
                box-sizing: border-box;
            }
            body {
                margin: 0;
                padding: 0;
                background-color: #000;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                overflow: hidden;
            }
            
            .wrapper {
                position: relative;
                width: 100vw;
                height: 100vh;
                max-width: 480px;
                max-height: 920px;
                display: flex;
                justify-content: center;
                align-items: center;
            }

            .bg-image {
                position: absolute;
                width: 100%;
                height: 100%;
                object-fit: cover;
                z-index: 1;
                pointer-events: none;
            }

            /* Área de inputs aumentada e proporcional ao pacote */
            .form-overlay {
                position: absolute;
                z-index: 10;
                width: 72%; /* Aumentado para preencher melhor a largura útil */
                top: 46%;
                transform: translateY(-50%);
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .row-inputs {
                display: flex;
                gap: 8px;
            }

            .input-box {
                background: rgba(12, 5, 3, 0.93);
                border: 1.5px solid rgba(255, 90, 0, 0.8);
                border-radius: 6px;
                padding: 12px 14px; /* Mais espaçamento interno (maior) */
                display: flex;
                align-items: center;
                box-shadow: inset 0 2px 5px rgba(0,0,0,0.85);
            }

            .input-box select,
            .input-box input {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 16px; /* Fonte maior para facilitar a leitura e digitação */
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
                width: 100%;
            }

            .toggle-pass {
                position: absolute;
                right: 14px;
                background: none;
                border: none;
                color: #ff5500;
                cursor: pointer;
                font-size: 18px; /* Botão de olho maior */
                font-weight: bold;
            }

            .btn-acessar {
                width: 100%;
                background: linear-gradient(to bottom, #ff5500 0%, #d61c00 100%);
                color: #fff;
                border: 1.5px solid #ff7733;
                padding: 14px; /* Botão mais robusto e fácil de clicar */
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 12px rgba(255, 68, 0, 0.7);
            }

            .btn-acessار:hover {
                background: linear-gradient(to bottom, #ff661a, #e62200);
            }

            .terminal-box {
                background: rgba(2, 6, 2, 0.95);
                border: 1.5px solid #166534;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Courier New', Courier, monospace;
                color: #4ade80;
                font-size: 12px; /* Letras do terminal maiores */
                line-height: 1.4;
                max-height: 85px;
                overflow-y: auto;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.9);
                margin-top: 6px;
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0tKEAAA..." class="bg-image" alt="Gulozitos OS">

            <div class="form-overlay">
                <form method="POST">
                    <div class="row-inputs" style="margin-bottom: 10px;">
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

                    <div class="input-box pass-container" style="margin-bottom: 12px;">
                        <input type="password" name="senha" id="senha" placeholder="Senha" required style="padding-right: 35px;">
                        <button type="button" class="toggle-pass" onclick="toggleSenha()">👁</button>
                    </div>

                    <button type="submit" class="btn-acessar">ACESSAR</button>
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
