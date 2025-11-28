import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .fabric_network import certidao
from typing import Dict, Optional

app = FastAPI(title="Blockchain Certidão API")

# ============== Models ==============

class CertCreate(BaseModel):
    cert_id: str
    nome: str
    data: str
    hora: str
    hospital: str
    pai: str
    mae: str
    cartorio: str
    cartorio_reg: str
    metadata: Dict[str, str]

class CertQuery(BaseModel):
    cert_id: str

class CertUpdate(BaseModel):
    cert_id: str
    field_name: str  # name, dateOfBirth, timeOfBirth, placeOfBirth, fatherName, motherName, owner, source
    new_value: str

# ============== Endpoints ==============

@app.post("/certidao/register")
async def register_cert(cert: CertCreate):
    """Registra uma nova certidão na blockchain"""
    try:
        metadata_json = json.dumps(cert.metadata)
        response = await certidao.register_cert(
            cert.cert_id,
            cert.nome,
            cert.data,
            cert.hora,
            cert.hospital,
            cert.pai,
            cert.mae,
            cert.cartorio,
            cert.cartorio_reg,
            metadata_json
        )
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/certidao/verify")
async def verify_cert(query: CertQuery):
    """Verifica uma certidão e retorna seus dados com validação de hash"""
    try:
        response = await certidao.verify_cert(query.cert_id)
        # Tenta parsear como JSON se for string
        if isinstance(response, (str, bytes)):
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                pass
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/certidao/history")
async def get_cert_history(query: CertQuery):
    """Retorna o histórico de alterações de uma certidão"""
    try:
        response = await certidao.get_history(query.cert_id)
        # Tenta parsear como JSON se for string
        if isinstance(response, (str, bytes)):
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                pass
        return {"status": "success", "history": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/certidao/update")
async def update_cert(update: CertUpdate):
    """Atualiza um campo específico de uma certidão"""
    try:
        response = await certidao.update_cert(
            update.cert_id,
            update.field_name,
            update.new_value
        )
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}