import os
import time
import json
import base64
import io
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
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
    
    executable_path = "/usr/bin/chromedriver"
    if not os.path.exists(executable_path):
        executable_path = "chromedriver"
        
    service = Service(executable_path=executable_path)
    return webdriver.Chrome(service=service, options=options)

def analisar_questao_com_ia(screenshot_bytes, log_status):
    """
    Envia a captura de tela da questão para o Gemini 2.5 Flash.
    A IA identifica o formato da pergunta (lacunas, múltipla escolha, VF ou texto)
    e retorna o gabarito preciso com instruções de preenchimento em JSON.
    """
    if not client:
        log_status.append("Erro: Chave GEMINI_KEY não configurada no ambiente.")
        return None

    try:
        log_status.append("IA analisando estrutura da imagem...")
        image_part = types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
        
        prompt_instrucao = """
        Você é um assistente acadêmico especialista em resolver tarefas escolares e vestibulares do CMSP / Sala do Futuro.
        Examine a imagem fornecida da questão.
        
        Sua tarefa é analisar o conteúdo visual e estrutural e responder estritamente em formato JSON válido com as seguintes chaves:
        {
          "tipo": "lacunas" | "multipla_escolha" | "verdadeiro_falso" | "dissertativa",
          "respostas_lacunas": ["palavra1", "palavra2"], 
          "opcao_correta": "texto ou índice exato da opção correta",
          "texto_dissertativo": "resposta redigida de forma clara e objetiva para questões abertas"
        }

        Diretrizes:
        1. Se for 'lacunas' (menus suspensos/dropdowns), forneça o texto exato das opções selecionáveis na ordem exata dos campos.
        2. Se for 'multipla_escolha' ou 'verdadeiro_falso', identifique a alternativa correta exatamente como escrita na tela.
        3. Se for 'dissertativa', gere um texto acadêmico conciso e correto para o campo de resposta.
        Retorne APENAS o JSON, sem marcações markdown como ```json.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt_instrucao]
        )
        
        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        dados_resposta = json.loads(raw_text)
        log_status.append(f"IA concluiu análise: Tipo [{dados_resposta.get('tipo', 'desconhecido')}]")
        return dados_resposta
    except Exception as e:
        log_status.append(f"Erro na análise de visão computacional: {str(e)[:50]}...")
        return None

def preencher_e_responder(driver, analise_ia, log_status):
    """
    Executa ações automatizadas no DOM baseadas na decisão da IA.
    """
    if not analise_ia:
        return False

    tipo = analise_ia.get("tipo")
    
    try:
        if tipo == "lacunas":
            respostas = analise_ia.get("respostas_lacunas", [])
            dropdowns = driver.find_elements(By.TAG_NAME, "select")
            
            if not dropdowns:
                # Caso a plataforma use custom dropdowns (divs/spans em vez de select nativo)
                custom_dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox'], .select-trigger, .dropdown-toggle")
                for idx, combo in enumerate(custom_dropdowns):
                    if idx < len(respostas):
                        combo.click()
                        time.sleep(0.5)
                        alvo = respostas[idx]
                        opcao = driver.find_element(By.XPATH, f"//*[contains(text(), '{alvo}')]")
                        opcao.click()
                        time.sleep(0.5)
            else:
                for idx, select_elem in enumerate(dropdowns):
                    if idx < len(respostas):
                        select_obj = Select(select_elem)
                        alvo = respostas[idx]
                        try:
                            select_obj.select_by_visible_text(alvo)
                        except:
                            # Fallback para busca parcial de texto
                            for option in select_obj.options:
                                if alvo.lower() in option.text.lower():
                                    select_obj.select_by_visible_text(option.text)
                                    break
            log_status.append("Lacunas preenchidas com sucesso.")

        elif tipo in ["multipla_escolha", "verdadeiro_falso"]:
            opcao_texto = analise_ia.get("opcao_correta", "")
            if opcao_texto:
                # Busca elementos clicáveis que contenham o texto da opção
                elementos = driver.find_elements(By.XPATH, f"//*[contains(text(), '{opcao_texto}')]")
                clicado = False
                for elem in elementos:
                    try:
                        if elem.is_displayed():
                            driver.execute_script("arguments[0].click();", elem)
                            clicado = True
                            break
                    except:
                        continue
                
                if not clicado:
                    # Tenta clicar no primeiro radio/checkbox correspondente
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
                    if inputs:
                        driver.execute_script("arguments[0].click();", inputs[0])
                log_status.append(f"Opção selecionada: '{opcao_texto[:20]}...'")

        elif tipo == "dissertativa":
            texto = analise_ia.get("texto_dissertativo", "")
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            if not textareas:
                textareas = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], [contenteditable='true']")
            
            if textareas:
                target = textareas[0]
                target.clear()
                target.send_keys(texto)
                log_status.append("Texto dissertativo inserido.")

        time.sleep(1)
        
        # Localiza e clica no botão de Enviar/Avançar/Responder
        botoes_acao = driver.find_elements(By.XPATH, "//button[contains(text(), 'Responder') or contains(text(), 'Enviar') or contains(text(), 'Avançar') or contains(text(), 'Próxima')]")
        if botoes_acao:
            for btn in botoes_acao:
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].click();", btn)
                    log_status.append("Resposta submetida. Avançando...")
                    break
        else:
            # Fallback para qualquer botão primário visível
            botoes_gerais = driver.find_elements(By.CSS_SELECTOR, "button.btn-primary, button[type='submit']")
            if botoes_gerais:
                driver.execute_script("arguments[0].click();", botoes_gerais[0])
                log_status.append("Ação de avanço executada.")

        return True
    except Exception as e:
        log_status.append(f"Aviso durante interacao no DOM: {str(e)[:40]}...")
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    log_status = [
        "GulozitosOS inicializado.",
        "Aguardando credenciais do usuario..."
    ]
    
    if request.method == "POST":
        ra_completo = request.form.get("ra_completo", "").strip()
        senha = request.form.get("senha", "").strip()
        acao = request.form.get("acao", "pendentes")
        
        nome_modo = "Atividades Pendentes" if acao == "pendentes" else "Atividades Expiradas"
        
        log_status = [
            f"Modo: {nome_modo}",
            f"Autenticando RA: {ra_completo}",
            "Iniciando navegador headless..."
        ]
        
        driver = None
        try:
            driver = iniciar_driver()
            log_status.append("Acessando portal Sala do Futuro...")
            driver.get("[https://saladofuturo.educacao.sp.gov.br/login-alunos](https://saladofuturo.educacao.sp.gov.br/login-alunos)")
            time.sleep(3)
            
            wait = WebDriverWait(driver, 12)
            
            # Preenchimento do formulário de login no portal
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if len(inputs) >= 2:
                inputs[0].clear()
                inputs[0].send_keys(ra_completo)
                inputs[1].clear()
                inputs[1].send_keys(senha)
                log_status.append("Credenciais inseridas nos campos.")
                
                # Clique no botão de Acessar / Entrar
                botoes_login = driver.find_elements(By.XPATH, "//button[@type='submit' or contains(text(), 'Entrar') or contains(text(), 'Acessar')]")
                if botoes_login:
                    botoes_login[0].click()
                    log_status.append("Efetuando login no sistema...")
                    time.sleep(5)
            
            # Navegação até a seção de tarefas
            log_status.append(f"Navegando até a lista de {nome_modo.lower()}...")
            
            if acao == "expiradas":
                links_expiradas = driver.find_elements(By.XPATH, "//*[contains(text(), 'Expiradas') or contains(text(), 'Fora do prazo')]")
                if links_expiradas:
                    driver.execute_script("arguments[0].click();", links_expiradas[0])
                    time.sleep(3)
            else:
                links_pendentes = driver.find_elements(By.XPATH, "//*[contains(text(), 'Pendentes') or contains(text(), 'A fazer')]")
                if links_pendentes:
                    driver.execute_script("arguments[0].click();", links_pendentes[0])
                    time.sleep(3)

            # Identificação das tarefas disponíveis
            cards_tarefas = driver.find_elements(By.CSS_SELECTOR, ".card-tarefa, .task-item, [role='button'], a[href*='tarefa']")
            log_status.append(f"Tarefas encontradas: {len(cards_tarefas)}")
            
            if cards_tarefas:
                # Entrar na primeira tarefa disponível
                driver.execute_script("arguments[0].click();", cards_tarefas[0])
                time.sleep(4)
                
                # Loop de resolução automática de questões (até 15 questões por atividade)
                max_questoes = 15
                for q in range(1, max_questoes + 1):
                    log_status.append(f"--- Processando Questão {q} ---")
                    
                    # Captura de tela da questão atual para visão computacional
                    screenshot = driver.get_screenshot_as_png()
                    
                    # Análise da IA
                    analise = analisar_questao_com_ia(screenshot, log_status)
                    
                    # Execução da resposta no navegador
                    sucesso = preencher_e_responder(driver, analise, log_status)
                    time.sleep(3)
                    
                    # Verificação se a tarefa foi finalizada ou se o botão de fim apareceu
                    fim = driver.find_elements(By.XPATH, "//*[contains(text(), 'Finalizado') or contains(text(), 'Concluído') or contains(text(), 'Nota')]")
                    if fim:
                        log_status.append("Atividade concluída com sucesso!")
                        break
            else:
                log_status.append("Nenhuma atividade pendente/expirada encontrada no momento.")

            log_status.append("Fluxo de automação encerrado.")
            
        except Exception as e:
            log_status.append(f"Processamento concluído com observação: {str(e)[:50]}...")
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
        <title>Gulozitos - Sala do Futuro</title>
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
                max-width: 420px;
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
                font-size: 34px;
                font-weight: 800;
                background: linear-gradient(135deg, #ff7a00 0%, #ffb347 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0 0 4px 0;
                letter-spacing: 0.5px;
            }

            .header p {
                font-size: 13px;
                color: #8f9bb3;
                margin: 0;
            }

            .card {
                background: rgba(18, 22, 38, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 24px;
                width: 100%;
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(12px);
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
                background: rgba(10, 13, 24, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.12);
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

            .btn-action {
                width: 100%;
                background: rgba(28, 33, 53, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.14);
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
                background: rgba(45, 54, 85, 1);
                border-color: #ff7a00;
            }

            .btn-action:active {
                transform: scale(0.98);
            }

            .terminal-box {
                background: rgba(4, 6, 12, 0.95);
                border: 1px solid #104523;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Courier New', Courier, monospace;
                color: #4ade80;
                font-size: 11px;
                line-height: 1.45;
                max-height: 120px;
                overflow-y: auto;
                margin-top: 15px;
                width: 100%;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Gulozitos</h1>
                <p>para sala do futuro e cmsp!</p>
            </div>

            <div class="card">
                <form method="POST" id="gulozitosForm">
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

                    <button type="submit" name="acao" value="pendentes" class="btn-action">Atividades Pendentes</button>
                    <button type="submit" name="acao" value="expiradas" class="btn-action">Atividades Expiradas</button>
                </form>

                <div class="terminal-box" id="termBox">
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
            
            const term = document.getElementById('termBox');
            term.scrollTop = term.scrollHeight;
        </script>
    </body>
    </html>
    """, logs_html=logs_html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
