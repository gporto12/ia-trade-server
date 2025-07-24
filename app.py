# Importa as bibliotecas necessárias
from flask import Flask, request, jsonify
import json
import datetime
import os
import google.generativeai as genai

# Cria uma instância do nosso aplicativo web
app = Flask(__name__)

# --- CONFIGURAÇÃO DA IA (GEMINI) ---
# Pega a chave de API das variáveis de ambiente do servidor (mais seguro)
# Teremos que configurar isso no Render
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
# ------------------------------------

def analisar_com_ia(strategy, ticker, price, timeframe):
    """
    Esta função envia os dados do sinal para a IA Gemini e pede uma análise.
    """
    try:
        print("🤖 Enviando dados para análise da IA...")

        # Monta a pergunta (prompt) para a IA.
        # Este é o "cérebro" da nossa validação. Podemos refinar este prompt no futuro.
        prompt = f"""
        Análise de Oportunidade de Trade:
        - Estratégia Identificada: {strategy}
        - Ativo: {ticker}
        - Preço de Sinal: {price}
        - Timeframe: {timeframe}

        Você é um analista de mercado experiente. Com base nesta informação e no seu conhecimento do contexto atual do mercado para este ativo, 
        avalie a qualidade desta entrada. Considere a força do movimento, possíveis zonas de suporte/resistência próximas e o sentimento geral.

        Responda em DUAS PARTES OBRIGATÓRIAS:
        1.  **Análise:** Um parágrafo curto (máximo de 3 frases) com sua opinião técnica.
        2.  **Confiança:** Uma nota de 0 a 10 sobre a sua confiança nesta operação.
        """

        # Envia o prompt para o modelo Gemini
        response = model.generate_content(prompt)
        
        print("✅ Análise da IA recebida!")
        return response.text

    except Exception as e:
        print(f"❌ ERRO na comunicação com a IA: {e}")
        return "Erro ao analisar com a IA."


@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Esta função é acionada toda vez que o TradingView envia um alerta.
    """
    print("------------------------------------------")
    print(f"Alerta recebido em: {datetime.datetime.now()}")

    try:
        data = request.get_json()
        print(f"Dados brutos recebidos: {json.dumps(data, indent=2)}")

        strategy = data.get('strategy', 'N/A')
        ticker = data.get('ticker', 'N/A')
        price = data.get('price', 'N/A')
        timeframe = data.get('timeframe', 'N/A')

        print(f"✅ SINAL RECEBIDO: {strategy} em {ticker}")

        # **NOVA ETAPA: Chamar a função de análise da IA**
        analise_ia = analisar_com_ia(strategy, ticker, price, timeframe)
        
        # Imprime o resultado da análise nos logs
        print("\n--- ANÁLISE DA IA ---")
        print(analise_ia)
        print("---------------------\n")
        
        # **PRÓXIMO PASSO SERÁ AQUI:**
        # Com a 'analise_ia' em mãos, vamos chamar a função que envia a notificação via Firebase.
        # ex: enviar_notificacao(analise_ia)

        return jsonify(status="sucesso", mensagem="Alerta recebido e analisado pela IA"), 200

    except Exception as e:
        print(f"❌ ERRO ao processar o alerta: {e}")
        return jsonify(status="erro", mensagem=str(e)), 400

# Esta parte não muda
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
