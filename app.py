import datetime
from typing import Dict, Any, List
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Neighborhood(db.Model):
    __tablename__ = 'neighborhood'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)

    measurements = db.relationship('Measurement', back_populates='neighborhood', cascade='all, delete-orphan')


class Measurement(db.Model):
    __tablename__ = 'measurement'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)

    clima = db.Column(db.JSON, nullable=True)
    qualidade_do_ar = db.Column(db.JSON, nullable=True)
    qualidade_da_agua = db.Column(db.JSON, nullable=True)
    riscos = db.Column(db.JSON, nullable=True)

    neighborhood_id = db.Column(db.Integer, db.ForeignKey('neighborhood.id'), nullable=False)
    neighborhood = db.relationship('Neighborhood', back_populates='measurements')

    __table_args__ = (
        db.UniqueConstraint('neighborhood_id', 'timestamp', name='uq_neigh_time'),
    )


@app.route('/')
def index():
    return jsonify({"msg": "Middleware ativo. Use POST /ingest para enviar dados."})


def _parse_timestamp(value: str) -> datetime.datetime:
    # Accept ISO8601 with optional 'Z' suffix
    if isinstance(value, str):
        v = value.replace('Z', '+00:00')
        try:
            return datetime.datetime.fromisoformat(v)
        except ValueError:
            pass
    raise ValueError('timestamp inválido, use ISO 8601 (ex.: 2025-10-20T14:30:00Z)')


def _ensure_neighborhood(name: str) -> Neighborhood:
    nb = Neighborhood.query.filter_by(name=name).first()
    if nb:
        return nb
    nb = Neighborhood(name=name)
    db.session.add(nb)
    db.session.flush()  # get id without full commit
    return nb


@app.route('/ingest', methods=['POST'])
def ingest():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    if 'bairros' not in payload or not isinstance(payload['bairros'], dict):
        return jsonify({"msg": "Corpo inválido: esperado objeto com chave 'bairros'"}), 400

    bairros = payload['bairros']

    created_neighborhoods = 0
    upserted_measurements = 0
    errors: List[Dict[str, Any]] = []

    for nome_bairro, lista_registros in bairros.items():
        if not isinstance(lista_registros, list):
            errors.append({"bairro": nome_bairro, "erro": "Valor deve ser uma lista"})
            continue

        # ensure/create neighborhood lazily; detect creation by checking transient state
        existing = Neighborhood.query.filter_by(name=nome_bairro).first()
        if existing is None:
            nb = _ensure_neighborhood(nome_bairro)
            created_neighborhoods += 1
        else:
            nb = existing

        for idx, registro in enumerate(lista_registros):
            if not isinstance(registro, dict):
                errors.append({"bairro": nome_bairro, "index": idx, "erro": "Registro deve ser um objeto"})
                continue
            try:
                ts = _parse_timestamp(registro.get('timestamp'))
            except Exception as e:
                errors.append({"bairro": nome_bairro, "index": idx, "erro": str(e)})
                continue

            clima = registro.get('clima')
            qualidade_do_ar = registro.get('qualidade_do_ar')
            qualidade_da_agua = registro.get('qualidade_da_agua')

            # Upsert by (neighborhood_id, timestamp)
            existing_m = Measurement.query.filter_by(neighborhood_id=nb.id, timestamp=ts).first()
            if existing_m:
                existing_m.clima = clima
                existing_m.qualidade_do_ar = qualidade_do_ar
                existing_m.qualidade_da_agua = qualidade_da_agua
            else:
                m = Measurement(
                    neighborhood_id=nb.id,
                    timestamp=ts,
                    clima=clima,
                    qualidade_do_ar=qualidade_do_ar,
                    qualidade_da_agua=qualidade_da_agua,
                )
                db.session.add(m)
            upserted_measurements += 1

    db.session.commit()

    return jsonify({
        "msg": "Dados ingeridos",
        "bairros_criados": created_neighborhoods,
        "medicoes_processadas": upserted_measurements,
        "erros": errors,
    }), 201


def _parse_day_to_dt(day: str) -> datetime.datetime:
    """Converte 'YYYY-MM-DD' para datetime em UTC (00:00)."""
    try:
        d = datetime.date.fromisoformat(day)
        return datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
    except Exception:
        raise ValueError("dia inválido, use formato YYYY-MM-DD")


@app.route('/ingest_v2', methods=['POST'])
def ingest_v2():
    """
    Aceita o novo formato diário:
    {
      "bairros": {
        "Nome do Bairro": {
          "YYYY-MM-DD": {
            "clima": {...},
            "qualidade_do_ar": {...},
            "qualidade_da_agua": {...},
            "riscos": { "clima": [], "qualidade_do_ar": [], "qualidade_da_agua": [] }
          }
        }
      }
    }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    if 'bairros' not in payload or not isinstance(payload['bairros'], dict):
        return jsonify({"msg": "Corpo inválido: esperado objeto com chave 'bairros'"}), 400

    bairros = payload['bairros']

    created_neighborhoods = 0
    upserted_measurements = 0
    errors: List[Dict[str, Any]] = []

    for nome_bairro, dias_obj in bairros.items():
        if not isinstance(dias_obj, dict):
            errors.append({"bairro": nome_bairro, "erro": "Valor deve ser um objeto de dias"})
            continue

        existing = Neighborhood.query.filter_by(name=nome_bairro).first()
        if existing is None:
            nb = _ensure_neighborhood(nome_bairro)
            created_neighborhoods += 1
        else:
            nb = existing

        for dia, dados in dias_obj.items():
            if not isinstance(dados, dict):
                errors.append({"bairro": nome_bairro, "dia": dia, "erro": "Dados do dia devem ser um objeto"})
                continue
            try:
                ts = _parse_day_to_dt(dia)
            except ValueError as e:
                errors.append({"bairro": nome_bairro, "dia": dia, "erro": str(e)})
                continue

            clima = dados.get('clima')
            qualidade_do_ar = dados.get('qualidade_do_ar')
            qualidade_da_agua = dados.get('qualidade_da_agua')
            riscos = dados.get('riscos')

            existing_m = Measurement.query.filter_by(neighborhood_id=nb.id, timestamp=ts).first()
            if existing_m:
                existing_m.clima = clima
                existing_m.qualidade_do_ar = qualidade_do_ar
                existing_m.qualidade_da_agua = qualidade_da_agua
                existing_m.riscos = riscos
            else:
                m = Measurement(
                    neighborhood_id=nb.id,
                    timestamp=ts,
                    clima=clima,
                    qualidade_do_ar=qualidade_do_ar,
                    qualidade_da_agua=qualidade_da_agua,
                    riscos=riscos,
                )
                db.session.add(m)
            upserted_measurements += 1

    db.session.commit()

    return jsonify({
        "msg": "Dados ingeridos (v2)",
        "bairros_criados": created_neighborhoods,
        "medicoes_processadas": upserted_measurements,
        "erros": errors,
    }), 201


@app.route('/bairros', methods=['GET'])
def list_bairros():
    items = Neighborhood.query.order_by(Neighborhood.name.asc()).all()
    return jsonify([{"id": n.id, "name": n.name} for n in items])


@app.route('/bairros/<string:nome>/medicoes', methods=['GET'])
def list_medicoes(nome: str):
    nb = Neighborhood.query.filter_by(name=nome).first()
    if not nb:
        return jsonify({"msg": "Bairro não encontrado"}), 404

    start = request.args.get('start')
    end = request.args.get('end')
    q = Measurement.query.filter_by(neighborhood_id=nb.id).order_by(Measurement.timestamp.asc())
    try:
        if start:
            q = q.filter(Measurement.timestamp >= _parse_timestamp(start))
        if end:
            q = q.filter(Measurement.timestamp <= _parse_timestamp(end))
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400

    data = [
        {
            "timestamp": m.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
            "clima": m.clima,
            "qualidade_do_ar": m.qualidade_do_ar,
            "qualidade_da_agua": m.qualidade_da_agua,
        }
        for m in q.all()
    ]
    return jsonify({"bairro": nb.name, "registros": data})


@app.route('/riscos', methods=['GET'])
def riscos():
    """
    Retorna os dados no formato novo, agrupados por dia, para todos os bairros.
    Exatamente a estrutura:
    {
      "bairros": { "Nome": { "YYYY-MM-DD": { ... } } }
    }
    """
    result: Dict[str, Any] = {"bairros": {}}

    bairros = Neighborhood.query.all()
    for nb in bairros:
        dias: Dict[str, Any] = {}
        regs: List[Measurement] = (
            Measurement.query
            .filter_by(neighborhood_id=nb.id)
            .order_by(Measurement.timestamp.asc())
            .all()
        )
        for m in regs:
            # normaliza para data (UTC)
            ts = m.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
            dia_str = ts.date().isoformat()
            dias[dia_str] = {
                "clima": m.clima,
                "qualidade_do_ar": m.qualidade_do_ar,
                "qualidade_da_agua": m.qualidade_da_agua,
                "riscos": m.riscos or {"clima": [], "qualidade_do_ar": [], "qualidade_da_agua": []},
            }
        result["bairros"][nb.name] = dias

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)