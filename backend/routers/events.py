from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Event
from datetime import datetime

router = APIRouter(prefix="/events", tags=["Eventos Reprodutivos"])

# Dependência padrão de sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def listar_eventos(db: Session = Depends(get_db)):
    eventos = db.query(Event).all()
    return {"ok": True, "data": eventos}


@router.post("/")
def criar_evento(animal_id: str, tipo: str, resultado: str, db: Session = Depends(get_db)):
    evento = Event(
        animal_id=animal_id,
        tipo=tipo,
        resultado=resultado,
        data_evento=datetime.utcnow(),
        tenant_id=1  # fixo por enquanto; depois vem autenticação multi-tenant
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return {"ok": True, "data": evento}
