# API Middleware SD

API middeware desenvolvida para a matéria de Sistemas Distribuídos.

## Requisitos

-   **Python 3.8 ou superior**
-   **Flask**

## Instruções para Instalação

### 1. Clone o repositório
`git clone https://github.com/davisouzal/sd-middeware-service.git`
`cd projeto-flask-prognostico` 

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

>Obs: Tabém pode rodar no modo debug:  `flask --app app --debug run`

Isso iniciará o servidor Flask em modo de desenvolvimento na porta `5000`. Acesse a aplicação via navegador no endereço `http://127.0.0.1:5000`.