from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

# 🧩 Tabela de clientes (cada clínica ou veterinário é um "tenant")
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    plan = Column(String, default="trial")
    status = Column(String, default="active")
    trial_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")


# 👤 Usuários (veterinários, técnicos, administradores)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="vet")
    is_active = Column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="users")


# 🐄 Eventos (ex: inseminação, FIV, parto)
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    animal_id = Column(String)
    tipo = Column(String)  # Ex: IA, FIV, Parto
    resultado = Column(String)
    data_evento = Column(DateTime)
