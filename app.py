# Importa o Flask e o objeto 'request' para lidar com as requisições web
from flask import Flask, request, jsonify
import json # Importa a biblioteca para lidar com JSON
import datetime # Importa a biblioteca para lidar com datas e horas

# Cria uma instância do nosso aplicativo web
app = Flask(__name__)

# Define a rota (o URL específico) que vai receber os alertas.
# O TradingView vai enviar os dados para 'seusite.com/webhook'
# O 'methods=['POST']' significa que esta rota só aceita dados enviados para ela.
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Esta função é acionada toda vez que o TradingView envia um alerta para o nosso URL.
    """
    print("------------------------------------------")
    print(f"Alerta recebido em: {datetime.datetime.now()}")

    try:
        # Pega os dados que o TradingView enviou (o JSON da nossa mensagem de alerta)
        data = request.get_json()
        print(f"Dados brutos recebidos: {json.dumps(data, indent=2)}")

        # Extrai as informações importantes do JSON
        strategy = data.get('strategy', 'N/A')
        ticker = data.get('ticker', 'N/A')
        price = data.get('price', 'N/A')
        timeframe = data.get('timeframe', 'N/A')

        # Imprime uma mensagem formatada no console (nos Logs do servidor) para sabermos que funcionou
        print(f"✅ SINAL RECEBIDO:")
        print(f"   - Estratégia: {strategy}")
        print(f"   - Ativo: {ticker}")
        print(f"   - Preço: {price}")
        print(f"   - Timeframe: {timeframe}")
        print("------------------------------------------\n")

        # **PRÓXIMO PASSO SERÁ AQUI:**
        # Neste ponto, no futuro, nós vamos chamar a função que fala com a IA
        # ex: ia_analysis_result = analisar_com_ia(strategy, ticker, price)

        # Retorna uma resposta de sucesso para o TradingView saber que recebemos o alerta.
        return jsonify(status="sucesso", mensagem="Alerta recebido"), 200

    except Exception as e:
        # Se algo der errado (ex: os dados não são JSON), imprime o erro
        print(f"❌ ERRO ao processar o alerta: {e}")
        # Retorna uma resposta de erro
        return jsonify(status="erro", mensagem=str(e)), 400

# Esta parte permite que o servidor seja iniciado quando executamos o arquivo
if __name__ == '__main__':
    # O host '0.0.0.0' é necessário para que o serviço funcione na nuvem
    # A porta é definida pelo serviço de hospedagem (ex: Render)
    app.run(host='0.0.0.0', port=5000)
