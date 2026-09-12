import os
import time
from flask import Flask, render_template_string, request
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

app = Flask(__name__)

# Configuração da API do Gemini usando a variável segura que você cadastrou na Render
GEMINI_API_KEY = os.environ.get("GEMINI_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def iniciar_driver():
  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-gpu")

  # Caminhos padrões do Chrome no ambiente Docker que configuramos
  service = Service(executable_path="/usr/bin/chromedriver")
  driver = webdriver.Chrome(service=service, options=options)
  return driver


@app.route("/", methods=["GET", "POST"])
def index():
  resultado = ""
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

      # Preenchendo os campos usando os IDs mapeados no site
      driver.find_element(By.ID, "input-usuario-sed").send_keys(ra)
      driver.find_element(By.ID, "r2").send_keys(digito)
      driver.find_element(By.ID, "input-senha").send_keys(senha)

      # Clicando no botão de login
      driver.find_element(By.ID, "botao-login").click()
      time.sleep(5)  # Aguarda o carregamento pós-login

      # Captura de tela para validação e uso futuro com o Gemini
      screenshot_path = "print_tela.png"
      driver.save_screenshot(screenshot_path)

      resultado = (
          "Login automatizado executado com sucesso e print capturado!"
      )
    except Exception as e:
      resultado = f"Erro ao executar o Selenium: {str(e)}"
    finally:
      if driver:
        driver.quit()

  # Template HTML da interface web
  return render_template_string(
      """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Gulozitos OS</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 320px; }
            h2 { text-align: center; color: #38bdf8; }
            input, select { width: 100%; padding: 10px; margin: 8px 0; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            button:hover { background: #0ea5e9; }
            .result { margin-top: 15px; font-size: 14px; text-align: center; color: #a3e635; word-break: break-word; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Gulozitos OS</h2>
            <form method="POST">
                <input type="text" name="ra" placeholder="RA do Aluno" required>
                <input type="text" name="digito" placeholder="Dígito" required>
                <input type="text" name="estado" placeholder="Estado (Ex: SP)" value="SP" required>
                <input type="password" name="senha" placeholder="Senha" required>
                <button type="submit">Entrar e Executar</button>
            </form>
            {% if resultado %}
                <div class="result">{{ resultado }}</div>
            {% endif %}
        </div>
    </body>
    </html>
    """,
      resultado=resultado,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

