from flask import Flask, request, jsonify
import json
import datetime
import os
import google.generativeai as genai
import requests
import firebase_admin
from firebase_admin import credentials, messaging

# =============================================================================
# INICIALIZAÇÃO E CONFIGURAÇÃO
# =============================================================================
app = Flask(__name__)

# --- Configuração do Firebase ---
try:
    # No Render, o arquivo secreto fica neste caminho
    cred = credentials.Certificate("/etc/secrets/firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK configurado com sucesso!")
except Exception as e:
    print(f"❌ ERRO ao configurar o Firebase: {e}. Verifique o 'Secret File' no Render.")

# --- Configuração da IA (Gemini) ---
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Modelo de IA Gemini configurado com sucesso!")
except Exception as e:
    print(f"❌ ERRO ao configurar a IA: {e}. Verifique a variável de ambiente 'GEMINI_API_KEY'.")

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def analisar_com_ia(strategy, ticker, price, timeframe):
    """Envia os dados do sinal para a IA Gemini e retorna a análise."""
    try:
        print("🤖 Enviando dados para análise da IA...")
        prompt = f"""
        Análise de Oportunidade de Trade:
        - Estratégia Identificada: {strategy}
        - Ativo: {ticker}
        - Preço de Sinal: {price}
        - Timeframe: {timeframe}

        Você é um analista de mercado experiente. Avalie a qualidade desta entrada com base no contexto atual do mercado para este ativo, 
        considerando força do movimento e possíveis suportes/resistências.

        Responda em DUAS PARTES OBRIGATÓRIAS:
        1.  **Análise:** Um parágrafo curto (máximo 3 frases) com sua opinião técnica.
        2.  **Confiança:** Uma nota de 0 a 10 sobre sua confiança na operação.
        """
        response = model.generate_content(prompt)
        print("✅ Análise da IA recebida!")
        return response.text
    except Exception as e:
        print(f"❌ ERRO na comunicação com a IA: {e}")
        return "Erro ao analisar com a IA."

def enviar_notificacao(titulo, corpo, topico="trade_alerts"):
    """Envia uma notificação push via FCM para um tópico."""
    try:
        print(f"📣 Enviando notificação para o tópico: {topico}...")
        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=corpo),
            topic=topico,
        )
        response = messaging.send(message)
        print('✅ Notificação enviada com sucesso:', response)
        return True
    except Exception as e:
        print(f'❌ ERRO ao enviar notificação: {e}')
        return False

# =============================================================================
# ROTA DE WEBHOOK DO TRADINGVIEW
# =============================================================================

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """Recebe o alerta do TradingView, analisa com a IA e envia a notificação."""
    print("------------------------------------------")
    print(f"Alerta de trade recebido em: {datetime.datetime.now()}")
    try:
        data = request.get_json()
        strategy = data.get('strategy', 'N/A')
        ticker = data.get('ticker', 'N/A')
        price = data.get('price', 'N/A')
        timeframe = data.get('timeframe', 'N/A')

        print(f"SINAL RECEBIDO: {strategy} em {ticker}")
        
        analise_ia = analisar_com_ia(strategy, ticker, price, timeframe)
        print("\n--- ANÁLISE DA IA ---\n" + analise_ia + "\n---------------------\n")
        
        titulo_notificacao = f"Alerta de Trade: {strategy} em {ticker}"
        corpo_notificacao = analise_ia
        enviar_notificacao(titulo_notificacao, corpo_notificacao)

        return jsonify(status="sucesso", mensagem="Alerta recebido, analisado e notificação enviada."), 200
    except Exception as e:
        print(f"❌ ERRO GERAL no webhook de trade: {e}")
        return jsonify(status="erro", mensagem=str(e)), 500

# =============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# =============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
