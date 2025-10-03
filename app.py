from flask import Flask, request, jsonify
import json
import datetime
import os
import google.generativeai as genai
import requests

app = Flask(__name__)

# --- CONFIGURAÇÕES E CHAVES DE API ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BASE44_API_KEY = os.getenv('BASE44_API_KEY')
BASE44_API_URL = os.getenv('BASE44_API_URL')

# Configura o modelo de IA
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Modelo de IA Gemini configurado.")
else:
    print("⚠️ Chave da API da Gemini não encontrada. A análise de IA está desativada.")

# --- LÓGICA DO WEBHOOK DE PAGAMENTO (ATUALIZADO) ---

def grant_user_access_on_base44(email_cliente):
    """Encontra um usuário na Base44 pelo email e atualiza seu plano."""
    if not BASE44_API_KEY or not BASE44_API_URL:
        return False, "Configuração da API da Base44 incompleta no servidor."

    headers = {'api_key': BASE44_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        # 1. Encontrar o ID do usuário pelo email
        print(f"Procurando usuário na Base44 com email: {email_cliente}")
        response = requests.get(BASE44_API_URL, headers=headers)
        response.raise_for_status()
        users = response.json()
        
        user_id = None
        for user in users:
            if user.get('email') and user.get('email').lower() == email_cliente.lower():
                user_id = user.get('entityId')
                print(f"✅ Usuário encontrado! ID: {user_id}")
                break
        
        if not user_id:
            return False, f"Usuário com email {email_cliente} não foi encontrado na Base44."

        # 2. Atualizar o plano do usuário
        update_url = f"{BASE44_API_URL}/{user_id}"
        
        # IMPORTANTE: Altere "Pro" abaixo se o nome do seu plano de assinante for diferente.
        update_payload = { "plan": "Pro" }
        
        print(f"Atualizando plano do usuário ID: {user_id} para '{update_payload['plan']}'...")
        update_response = requests.put(update_url, headers=headers, json=update_payload)
        update_response.raise_for_status()
        
        print("✅ Plano do usuário atualizado com sucesso na Base44!")
        return True, "Acesso liberado."

    except requests.exceptions.RequestException as e:
        return False, f"ERRO na API da Base44: {e}"

@app.route('/webhook-xgrow', methods=['POST'])
def xgrow_webhook():
    print("------------------------------------------")
    print(f"Webhook da XGrow recebido em: {datetime.datetime.now()}")
    try:
        data = request.get_json()
        # Assumindo que a XGrow envia o email do cliente no campo 'customer_email'
        email = data.get('customer_email')
        
        if not email:
            return jsonify(status="erro", mensagem="Email não encontrado no webhook."), 400
            
        print(f"Pagamento recebido para o email: {email}")
        success, message = grant_user_access_on_base44(email)
        
        if success:
            return jsonify(status="sucesso", mensagem=message), 200
        else:
            return jsonify(status="erro", mensagem=message), 500
    except Exception as e:
        return jsonify(status="erro", mensagem=str(e)), 400

# --- CÓDIGO ANTERIOR (WEBHOOK DE TRADE, ETC) ---
# ... (o restante do código para o webhook do TradingView e a IA continua aqui, sem alterações) ...
# ...
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    # ... código do webhook de trade ...
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
