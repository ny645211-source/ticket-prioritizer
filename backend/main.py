import os
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from nlp import analyze

# No Docker needed: uses a local SQLite file by default.
# Set DATABASE_URL to a postgresql:// URL to use PostgreSQL instead.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tickets.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    customer = Column(String(120), nullable=False)
    plan = Column(String(20), nullable=False, default="free")
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(40))
    sentiment = Column(Float)
    priority = Column(String(10))
    score = Column(Float)
    reasons = Column(Text)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


Base.metadata.create_all(engine)


class TicketIn(BaseModel):
    customer: str = Field(min_length=1, max_length=120)
    plan: Literal["free", "pro", "enterprise"] = "free"
    subject: str = Field(min_length=3, max_length=255)
    body: str = Field(min_length=3)


class TicketOut(BaseModel):
    id: int
    customer: str
    plan: str
    subject: str
    body: str
    category: Optional[str]
    sentiment: Optional[float]
    priority: Optional[str]
    score: Optional[float]
    reasons: Optional[str]
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class StatusIn(BaseModel):
    status: Literal["open", "in_progress", "resolved"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Ticket Prioritizer")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
                   allow_methods=["*"], allow_headers=["*"])


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketIn, db: Session = Depends(get_db)):
    result = analyze(data.subject, data.body, data.plan)
    ticket = Ticket(**data.model_dump(), **result)
    db.add(ticket); db.commit(); db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(status: str = "open", limit: int = 100, db: Session = Depends(get_db)):
    """Returns the queue sorted by priority score, with age boost applied."""
    rows = db.query(Ticket).filter(Ticket.status == status).all()
    now = datetime.now(timezone.utc)
    for t in rows:  # re-score so waiting tickets rise over time
        created = t.created_at
        if created.tzinfo is None:  # SQLite returns naive UTC times
            created = created.replace(tzinfo=timezone.utc)
        age = (now - created).total_seconds() / 3600
        r = analyze(t.subject, t.body, t.plan, age)
        t.score, t.priority, t.reasons = r["score"], r["priority"], r["reasons"]
    db.commit()
    rows.sort(key=lambda t: t.score or 0, reverse=True)
    return rows[:limit]


@app.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: int, data: StatusIn, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    ticket.status = data.status
    db.commit(); db.refresh(ticket)
    return ticket


@app.get("/health")
def health():
    return {"ok": True}
