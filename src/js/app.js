const stateSelect = document.getElementById("state");
const citySelect = document.getElementById("city");
const searchButton = document.getElementById("search");
const resultDiv = document.getElementById("result");
const airQualityText = document.getElementById("air-quality");
const errorDiv = document.getElementById("error");
const ctx = document.getElementById('line-chart');

const BASE_URL = "http://127.0.0.1:5000";
const IQAIR_API_KEY = "beb8baa4-a648-4154-bf21-f8c49c58141d";

let isGeoLocation = false; // Variável de controle para identificar o fluxo

// Função para inicializar a página
window.onload = async () => {
    try {
        console.log("caiu")
        await loadStates(); // Carrega estados para seleção
        await getUserLocation(); // Busca geolocalização do usuário
        await atualizarDados(); // Primeiro, atualiza os dados no banco
        initChart();
    } catch (err) {
        showError(err.message);
    }
};

// Carregar estados na inicialização
const loadStates = async () => {
    try {
        const response = await fetch(`${BASE_URL}/states?country=Brazil`);
        if (!response.ok) throw new Error("Erro ao carregar estados.");
        const data = await response.json();

        // Adiciona estados ao dropdown
        data.states.forEach((state) => {
            const option = document.createElement("option");
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    } catch (err) {
        showError("Não foi possível carregar os estados.");
    }
};

// Carregar cidades ao selecionar estado
stateSelect.addEventListener("change", async () => {
    const state = stateSelect.value;
    citySelect.innerHTML = '<option value="">Selecione uma cidade</option>';
    citySelect.disabled = true;
    searchButton.disabled = true;

    if (!state) return;

    try {
        const response = await fetch(`${BASE_URL}/cities?state=${state}&country=Brazil`);
        if (!response.ok) throw new Error("Erro ao carregar cidades. Tente outra cidade.");
        const data = await response.json();

        data.cities.forEach((city) => {
            const option = document.createElement("option");
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });

        citySelect.disabled = false;
    } catch (err) {
        showError("Erro ao carregar cidades. Tente outra cidade.");
    }
});

// Ativar botão de busca ao selecionar cidade
citySelect.addEventListener("change", () => {
    searchButton.disabled = !citySelect.value;
});

// Buscar dados de qualidade do ar e temperatura
const fetchAirQuality = async (state, city) => {
    try {
        const response = await fetch(`${BASE_URL}/air-quality?state=${state}&city=${city}&country=Brazil`);
        if (!response.ok) throw new Error("Erro ao buscar qualidade do ar.");
        const data = await response.json();
        console.log("data: " + JSON.stringify(data));

        const temperature = data?.air_quality?.weather?.tp ?? "25"
        airQualityText.innerHTML = `
            Local: ${city}, ${state}<br>
            Temperatura: ${temperature}°C<br>
            Índice de qualidade do ar (AQI): ${data.air_quality.aqius}<br>
            Principal poluente: ${data.air_quality.mainus}
        `;
        // resultDiv.classList.remove("hidden");
        // errorDiv.classList.add("hidden");

        showSuccess(); 
    } catch (err) {
        console.log("err: " + JSON.stringify(err));
        showError("Erro ao buscar os dados de qualidade do ar.");
    } finally {
        isGeoLocation = false; // Reset após a execução
    }
};

// Função para exibir erros
const showError = (message) => {
    errorDiv.textContent = message;
    errorDiv.classList.remove("hidden");
    resultDiv.classList.add("hidden");
};

const showSuccess = () => {
    errorDiv.classList.add("hidden");
    resultDiv.classList.remove("hidden");
};

// Buscar localização e dados de qualidade do ar
const getUserLocation = async () => {
    isGeoLocation = true;
    if (!navigator.geolocation) {
        showError("Geolocalização não é suportada no seu navegador.");
        isGeoLocation = false;
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            try {
                const response = await fetch(`${BASE_URL}/nearest_city?lat=${latitude}&lon=${longitude}&key=${IQAIR_API_KEY}`);
                if (!response.ok) throw new Error("Erro ao obter dados de localização.");
                const data = await response.json();

                const city = data.data.city;
                const state = data.data.state;
                const temperature = data?.data?.current?.weather?.tp ?? "25"
                const aqi = data.data.current.pollution.aqius;
                const mainPollutant = data.data.current.pollution.mainus;

                airQualityText.innerHTML = `
                    Local: ${city}, ${state}<br>
                    Temperatura: ${temperature}°C<br>
                    Índice de qualidade do ar (AQI): ${aqi}<br>
                    Principal poluente: ${mainPollutant}
                `;
                resultDiv.classList.remove("hidden");
                errorDiv.classList.add("hidden");
                showSuccess(); 
            } catch (err) {
                showError("Erro ao buscar dados automáticos.");
            } finally {
                isGeoLocation = false;
            }
        },
        (error) => {
            isGeoLocation = false;
            showError("Permissão de geolocalização negada.");
        }
    );
};

// Evento para busca manual
searchButton.addEventListener("click", async () => {
    event.preventDefault(); // Previne o comportamento padrão de recarregar a página

    if (isGeoLocation) {
        showError("Aguarde a conclusão da geolocalização.");
        return;
    }

    const state = stateSelect.value;
    const city = citySelect.value;

    if (!state || !city) {
        showError("Selecione um estado e uma cidade.");
        return;
    }

    await fetchAirQuality(state, city);
});


async function fetchData() {

    const response = await fetch(`${BASE_URL}/api/energia`); // Altere o endpoint conforme necessário
    const data = await response.json();
    return data;
}

async function atualizarDados() {
    try {
        const response = await fetch(`${BASE_URL}/api/atualizar-dados`, {
            method: 'POST'
        });
        const result = await response.json();
        console.log(result.message); // "Dados atualizados com sucesso!"
    } catch (error) {
        console.error('Erro ao atualizar os dados:', error);
    }
}

// Função para inicializar o gráfico
async function initChart() {
    const apiData = await fetchData();

    const labels = apiData.map(item => item.data); // Datas
    const valores = apiData.map(item => item.valor); // Valores


    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels, // Dados dinâmicos para os labels
            datasets: [{
                label: 'Geração de Energia Renovável (kWh)',
                data: valores, // Dados dinâmicos para os valores
                borderWidth: 1,
                backgroundColor: '#E3FF47',
                borderColor: '#E3FF47',
                pointHoverBackgroundColor: '#FFFFFF',
            }]
        },
        options: {
            scales: {
                x: {
                    grid: {
                        color: 'grey'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'grey'
                    }
                }
            },
        }
    });
}
