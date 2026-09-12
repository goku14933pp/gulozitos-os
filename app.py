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
    resultado = "Inicializando GulozitosOS..."
    if request.method == "POST":
        ra = request.form.get("ra")
        digito = request.form.get("digito")
        estado = request.form.get("estado")
        senha = request.form.get("senha")
        
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
            resultado = "Login automatizado executado com sucesso!"
        except Exception as e:
            resultado = f"Erro: {str(e)}"
        finally:
            if driver: driver.quit()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Gulozitos OS</title>
        <style>
            body {
                background-color: #121212;
                background-image: radial-gradient(#2a2a2a 1px, transparent 1px);
                background-size: 20px 20px;
                color: #fff;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .main-card {
                background: #000;
                border: 2px solid #ff3b00;
                border-radius: 8px;
                padding: 25px 20px;
                width: 340px;
                box-shadow: 0 10px 30px rgba(255, 59, 0, 0.3);
                position: relative;
            }
            .logo-container {
                text-align: center;
                margin-bottom: 20px;
            }
            .logo-text {
                font-family: 'Impact', sans-serif;
                font-size: 32px;
                color: #ffcc00;
                letter-spacing: 2px;
                text-shadow: 2px 2px #ff3b00;
                font-style: italic;
            }
            .row-inputs {
                display: flex;
                gap: 10px;
                margin-bottom: 12px;
            }
            .input-group {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
            }
            .input-group input, .input-group select {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 16px;
                width: 100%;
                outline: none;
            }
            .input-group select option {
                background: #1a1a1a;
                color: #fff;
            }
            .ra-box { flex: 3; }
            .digito-box { flex: 1; }
            .pass-container {
                position: relative;
            }
            .toggle-pass {
                background: none;
                border: none;
                color: #888;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-acessar {
                width: 100%;
                background: #ff5500;
                color: #fff;
                border: none;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 5px;
                transition: background 0.2s;
            }
            .btn-acessar:hover {
                background: #ff7722;
            }
            .terminal-box {
                background: #080f08;
                border: 1px solid #1e4620;
                border-radius: 6px;
                padding: 12px;
                margin-top: 20px;
                font-family: 'Courier New', Courier, monospace;
                color: #4ade80;
                font-size: 13px;
                min-height: 40px;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="main-card">
            <div class="logo-container">
                <span class="logo-text">Gulozitos</span>
            </div>
            
            <form method="POST">
                <div class="row-inputs">
                    <div class="input-group ra-box">
                        <input type="text" name="ra" placeholder="RA do Aluno" required>
                    </div>
                    <div class="input-group digito-box">
                        <input type="text" name="digito" placeholder="Dígito" maxlength="2" required>
                    </div>
                </div>

                <div class="input-group">
                    <select name="estado" required>
                        <option value="" disabled selected>Selecione o Estado</option>
                        <option value="SP">São Paulo (SP)</option>
                        <option value="RJ">Rio de Janeiro (RJ)</option>
                        <option value="MG">Minas Gerais (MG)</option>
                        <option value="RS">Rio Grande do Sul (RS)</option>
                        <option value="PR">Paraná (PR)</option>
                        <option value="SC">Santa Catarina (SC)</option>
                        <option value="BA">Bahia (BA)</option>
                        <option value="Outros">Outros Estados</option>
                    </select>
                </div>

                <div class="input-group pass-container">
                    <input type="password" name="senha" id="senha" placeholder="Senha" required>
                    <button type="button" class="toggle-pass" onclick="togglePassword()">👁️</button>
                </div>

                <button type="submit" class="btn-acessar">ACESSAR</button>
            </form>

            <div class="terminal-box">
                > {{ resultado }}
            </div>
        </div>

        <script>
            function togglePassword() {
                const passInput = document.getElementById('senha');
                if (passInput.type === 'password') {
                    passInput.type = 'text';
                } else {
                    passInput.type = 'password';
                }
            }
        </script>
    </body>
    </html>
    """, resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
