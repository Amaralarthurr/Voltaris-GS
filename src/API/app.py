from flask import Flask, request, jsonify,render_template
import requests
import pymysql  # ou cx_Oracle para Oracle
from datetime import datetime, timedelta
import random
# Criação da aplicação Flask
app = Flask(
    __name__,
    template_folder="../../templates",  # Caminho relativo para a pasta templates
    static_folder="../../styles"       # Caminho relativo para a pasta static (CSS, JS, etc.)
)


# Endpoints das APIs
IQAIR_BASE_URL = "http://api.airvisual.com/v2/"
IQAIR_API_KEY = "beb8baa4-a648-4154-bf21-f8c49c58141d"
PVWATTS_BASE_URL = "https://developer.nrel.gov/api/pvwatts/v6.json"
PVWATTS_API_KEY = "9Z3hBJ892h0kpWeNPEnvoF9BlouVqf1cqIm7B7Gf"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'gs2024',
    'database': 'energia_db'
}

# Função para salvar os dados no banco
def salvar_dados_no_banco(dados):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            for dado in dados:
                query = """
                INSERT INTO energia (data, energia_gerada, tipo_energia, valor)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE energia_gerada = VALUES(energia_gerada), valor = VALUES(valor);
                """
                cursor.execute(query, (dado['data'], dado['energia_gerada'], dado['tipo_energia'], dado['valor']))
        connection.commit()
    finally:
        connection.close()

# Função para gerar dados fictícios
def gerar_dados_ficticios():
    hoje = datetime.now()
    dados_ficticios = []
    
    for i in range(7):
        data = hoje - timedelta(days=i)
        dado = {
            'data': data.strftime('%Y-%m-%d'),
            'energia_gerada': round(random.uniform(100.0, 500.0), 2),  # Valores entre 100 e 500
            'tipo_energia': random.choice(['solar', 'eólica', 'hídrica']),  # Escolha aleatória
            'valor': round(random.uniform(50.0, 300.0), 2)  # Valor fictício entre 50 e 300
        }
        dados_ficticios.append(dado)
    
    return dados_ficticios

# Gera e salva os dados no banco
if __name__ == "__main__":
    dados_ficticios = gerar_dados_ficticios()
    salvar_dados_no_banco(dados_ficticios)
    print("Dados fictícios gerados e salvos no banco com sucesso!")


@app.route("/")
def index():
    return render_template("index.html")  # Certifique-se de que este é o nome correto do seu arquivo HTML.


# Endpoint para atualizar os dados no banco
@app.route('/api/atualizar-dados', methods=['POST'])
def atualizar_dados():
    dados_ficticios = gerar_dados_ficticios()
    salvar_dados_no_banco(dados_ficticios)
    return jsonify({"message": "Dados atualizados com sucesso!"})

# Endpoint para buscar dados do banco
@app.route('/api/energia', methods=['GET'])
def get_dados():
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            query = "SELECT data, energia_gerada, tipo_energia, valor FROM energia ORDER BY data DESC LIMIT 7;"
            cursor.execute(query)
            rows = cursor.fetchall()
            dados = [{'data': row[0], 'energia_gerada': row[1], 'tipo_energia': row[2], 'valor': row[3]} for row in rows]
        return jsonify(dados)
    finally:
        connection.close()



# Função para calcular a pegada de carbono
def calcular_pegada(transporte, energia, alimentacao, residuos):
    # Emissões médias (valores fictícios para exemplo)
    emissoes_transporte = {
        "carro": 0.21,  # kg CO2 por km
        "transporte_publico": 0.10,  # kg CO2 por km
        "bicicleta": 0  # Sem emissão
    }
    emissoes_alimentacao = {
        "carnivoro": 2.5,  # kg CO2 por dia
        "vegetariano": 1.5  # kg CO2 por dia
    }
    
    # Cálculos
    emissao_transporte = emissoes_transporte.get(transporte, 0) * 30  # Supondo 30 km/dia
    emissao_energia = energia * 0.233  # kg CO2 por KWh
    emissao_alimentacao = emissoes_alimentacao.get(alimentacao, 0) * 30  # 30 dias
    emissao_residuos = residuos * 0.5  # kg CO2 por kg de resíduo
    
    # Soma total de emissões
    total_emissoes = emissao_transporte + emissao_energia + emissao_alimentacao + emissao_residuos
    return total_emissoes

# Rota para cálculo da pegada de carbono
@app.route("/calcular-pegada", methods=["POST"])
def calcular_pegada():
    # Captura os dados do formulário
    nome = request.form.get("nome-funcionario")
    transporte = request.form.get("transporte")
    energia = float(request.form.get("energia", 0))
    alimentacao = request.form.get("alimentacao")
    residuos = float(request.form.get("residuos", 0))
    
    # Cálculo da pegada de carbono (exemplo)
    transporte_emissao = {
        "carro": 0.21,  # Emissões por km (exemplo)
        "transporte público": 0.05,
        "bicicleta": 0
    }
    alimentacao_emissao = {
        "carnivoro": 1.5,  # Emissões anuais por pessoa (exemplo)
        "vegetariano": 0.9
    }
    
    # Pegada de carbono total (simplificada)
    pegada = (
        transporte_emissao.get(transporte, 0) * 100 +  # Suponha 100 km por mês
        energia * 0.233 +  # Emissões por kWh
        alimentacao_emissao.get(alimentacao, 0) +
        residuos * 0.02  # Emissões por kg de resíduos
    )
    
    # Retorna o resultado
    return render_template("resultado.html", nome=nome, pegada=pegada)

# Rota inicial
# @app.route('/')
# def index():
#     return "API de Cálculo de Pegada de Carbono. Use a rota /calcular para enviar dados."



# Rota para listar estados
@app.route('/states', methods=['GET'])
def list_states():
    country = request.args.get('country', 'Brazil')  # Define o país padrão como Brasil
    try:
        url = f"{IQAIR_BASE_URL}states?country={country}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        states = [state['state'] for state in data['data']]
        return jsonify({"country": country, "states": states}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro ao buscar estados.", "details": str(e)}), 500

# Rota para listar cidades de um estado
@app.route('/cities', methods=['GET'])
def list_cities():
    state = request.args.get('state')
    country = request.args.get('country', 'Brazil')  # Define o país padrão como Brasil
    if not state:
        return jsonify({"error": "O parâmetro 'state' é obrigatório."}), 400

    try:
        url = f"{IQAIR_BASE_URL}cities?state={state}&country={country}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        cities = [city['city'] for city in data['data']]
        return jsonify({"state": state, "country": country, "cities": cities}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro ao buscar cidades.", "details": str(e)}), 500

# Rota para obter qualidade do ar
@app.route('/air-quality', methods=['GET'])
def air_quality():
    state = request.args.get('state')
    city = request.args.get('city')
    country = request.args.get('country', 'Brazil')

    if not state or not city:
        return jsonify({"error": "Os parâmetros 'state' e 'city' são obrigatórios."}), 400

    try:
        url = f"{IQAIR_BASE_URL}city?city={city}&state={state}&country={country}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "city": city,
            "state": state,
            "air_quality": data['data']['current']['pollution']
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro ao obter dados de qualidade do ar.", "details": str(e)}), 500


# Rota para calcular energia solar
@app.route('/solar-energy', methods=['POST'])
def solar_energy():
    try:
        payload = request.json
        payload['api_key'] = PVWATTS_API_KEY

        response = requests.post(PVWATTS_BASE_URL, params=payload)
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "location": payload.get('address', 'Desconhecido'),
            "monthly_energy": data['outputs']['ac_monthly']
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro ao calcular energia solar.", "details": str(e)}), 500


@app.route('/nearest_city', methods=['GET'])
def nearest_city():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({"error": "Latitude e longitude são obrigatórios."}), 400

    try:
        url = f"http://api.airvisual.com/v2/nearest_city?lat={lat}&lon={lon}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Erro ao obter dados da cidade mais próxima.", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
