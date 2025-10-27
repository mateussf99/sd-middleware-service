# API Middleware SD

Middleware para ingestão e exposição de dados ambientais por bairro.

## Requisitos

-   **Python 3.8 ou superior**
-   **Flask**

## Instruções para Instalação

### 1. Clone o repositório
`git clone https://github.com/davisouzal/sd-middeware-service.git`
`cd sd-middleware-service` 

### 2. Crie um ambiente virtual (recomendado)

#### No Windows:

`python -m venv venv`
`venv\Scripts\activate` 

#### No Linux:

`python3 -m venv venv`
`source venv/bin/activate` 

### 3. Instale as dependências

Com o ambiente virtual ativado, execute:

`pip install -r requirements.txt` 

> Nota: Certifique-se de que o arquivo `requirements.txt` contenha as bibliotecas necessárias, como Flask e outras.

## Executando a aplicação

Após instalar as dependências, você pode iniciar a aplicação localmente.

#### No Windows:

`set FLASK_APP=app`
`set FLASK_ENV=development`
`flask run`

#### No Linux:
`export FLASK_APP=app`
`export FLASK_ENV=development`
`flask run` 

>Obs: Também pode rodar no modo debug:  `flask --app app --debug run`

Isso iniciará o servidor Flask em modo de desenvolvimento na porta `5000`. Acesse a aplicação via navegador no endereço `http://127.0.0.1:5000`.

## Banco de dados e migrações (Windows)

Após mudanças de modelo (ex.: novo campo `riscos`), você precisa gerar/aplicar migrações.

Passo a passo usando PowerShell e o ambiente virtual do projeto:

```
# 1) Ative o venv do projeto (se ainda não estiver ativo)
./venv/Scripts/Activate.ps1

# 2) Configure as variáveis do Flask (somente nesta sessão)
$env:FLASK_APP = "app"
$env:FLASK_ENV = "development"

# 3) Gere a migração (se ainda não existir) e aplique
flask --app app db migrate -m "Auto migration"
flask --app app db upgrade
```

Remigração completa (apagar e recriar estrutura) — útil em desenvolvimento:

```
py remigrate.py
```

Esse script:
- remove `instance/`, `migrations/` e `app.db`
- roda `flask --app app db init/migrate/upgrade`

## Endpoints

- GET `/` — status do middleware
- POST `/ingest` — ingere dados dos sensores
- POST `/ingest_v2` — ingere dados do back
- GET `/bairros` — lista bairros cadastrados
- GET `/bairros/<nome>/medicoes` — lista medições de um bairro (opcionalmente filtrando por intervalo de tempo)
- GET `/riscos` — retorna todos os dados no formato v2 pronto para o front

### Formato esperado para POST /ingest (v1)

Exemplo de payload:

```
{
	"bairros": {
		"Nome do Bairro": [
			{
				"timestamp": "2025-10-20T14:30:00Z",
				"clima": {
					"temperatura_ar": 25.5,
					"umidade_relativa": 68.0,
					"precipitacao": 0.0,
					"cobertura_vegetal": 55.2
				},
				"qualidade_do_ar": {
					"material_particulado_pm25": 30.1,
					"monoxido_carbono": 1.5
				},
				"qualidade_da_agua": {
					"ph_agua": 7.2,
					"turbidez": 1.8,
					"coliformes_totais": 150,
					"cloro_residual": 0.5
				}
			}
		]
	}
}
```

Notas:
- `timestamp` deve estar em ISO 8601. O sufixo `Z` é aceito (UTC).
- O serviço realiza upsert por `(bairro, timestamp)`: se já existir, atualiza os blocos `clima`, `qualidade_do_ar` e `qualidade_da_agua`.

### Formato esperado para POST /ingest_v2 (recomendado)

Exemplo de payload diário por bairro e dia (YYYY-MM-DD), incluindo `riscos`:

```
{
	"bairros": {
		"Nome do Bairro": {
			"2025-10-20": {
				"clima": {
					"temperatura_ar": 26.1,
					"umidade_relativa": 70.5,
					"precipitacao": 0.1,
					"cobertura_vegetal": 55.2
				},
				"qualidade_do_ar": {
					"material_particulado_pm25": 45.8,
					"monoxido_carbono": 3.1
				},
				"qualidade_da_agua": {
					"ph_agua": 7.1,
					"turbidez": 2.5,
					"coliformes_totais": 300,
					"cloro_residual": 0.8
				},
				"riscos": {
					"clima": ["Condições climáticas normais"],
					"qualidade_do_ar": ["PM2.5 moderado"],
					"qualidade_da_agua": []
				}
			}
		}
	}
}
```

Notas:
- A chave do dia deve estar em formato `YYYY-MM-DD` e será armazenada como `timestamp` às 00:00 UTC daquele dia.
- O serviço realiza upsert por `(bairro, timestamp)`: se já existir, atualiza `clima`, `qualidade_do_ar`, `qualidade_da_agua` e `riscos`.

### Saída de GET /riscos

Retorna exatamente o mesmo formato do v2, consolidando todos os bairros e dias:

```
{
	"bairros": {
		"Nome do Bairro": {
			"YYYY-MM-DD": {
				"clima": { ... },
				"qualidade_do_ar": { ... },
				"qualidade_da_agua": { ... },
				"riscos": { "clima": [], "qualidade_do_ar": [], "qualidade_da_agua": [] }
			}
		}
	}
}
```
