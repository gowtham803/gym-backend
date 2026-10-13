from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timedelta

# Database Setup
engine = create_engine("sqlite:///gym.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    member_id = Column(String, default="ITK-1000")
    phone = Column(String, default="+91 ")
    duration = Column(String, default="1 Month")
    start_date = Column(String)   # YYYY-MM-DD
    expiry_date = Column(String)  # YYYY-MM-DD
    status = Column(String, default="ACTIVE")

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_expiry(start_date_str: str, duration: str) -> str:
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except Exception:
        start = date.today()
    
    if "1 Month" in duration:
        expiry = start + timedelta(days=30)
    elif "3 Month" in duration:
        expiry = start + timedelta(days=90)
    elif "6 Month" in duration:
        expiry = start + timedelta(days=180)
    elif "1 Year" in duration:
        expiry = start + timedelta(days=365)
    else:
        expiry = start + timedelta(days=30)
    return expiry.strftime("%Y-%m-%d")

def compute_member_status(m: Member) -> dict:
    today = date.today()
    if m.status == "FROZEN":
        current_status = "FROZEN"
    else:
        try:
            exp = datetime.strptime(m.expiry_date, "%Y-%m-%d").date()
            days_left = (exp - today).days
            if days_left < 0:
                current_status = "EXPIRED"
            elif days_left <= 7:
                current_status = "EXPIRING"
            else:
                current_status = "ACTIVE"
        except Exception:
            current_status = m.status or "ACTIVE"
            days_left = 0

    try:
        exp = datetime.strptime(m.expiry_date, "%Y-%m-%d").date()
        days_left = (exp - today).days
    except Exception:
        days_left = 0

    return {
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "member_id": m.member_id,
        "phone": m.phone,
        "duration": m.duration,
        "start_date": m.start_date,
        "expiry_date": m.expiry_date,
        "days_left": days_left,
        "status": current_status
    }

class MemberInput(BaseModel):
    name: str
    email: str
    member_id: Optional[str] = None
    phone: Optional[str] = "+91 "
    duration: Optional[str] = "1 Month"
    start_date: Optional[str] = None
    status: Optional[str] = "ACTIVE"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/members")
def get_members(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Member)
    if search:
        s = f"%{search}%"
        query = query.filter((Member.name.ilike(s)) | (Member.email.ilike(s)) | (Member.member_id.ilike(s)))
    
    records = query.all()
    results = [compute_member_status(m) for m in records]

    if status and status.upper() != "ALL":
        results = [r for r in results if r["status"].upper() == status.upper()]
    return results

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    all_members = [compute_member_status(m) for m in db.query(Member).all()]
    return {
        "total": len(all_members),
        "active": sum(1 for m in all_members if m["status"] == "ACTIVE"),
        "expiring": sum(1 for m in all_members if m["status"] == "EXPIRING"),
        "expired": sum(1 for m in all_members if m["status"] == "EXPIRED"),
        "frozen": sum(1 for m in all_members if m["status"] == "FROZEN"),
    }

@app.post("/members")
def add_member(data: MemberInput, db: Session = Depends(get_db)):
    st_date = data.start_date or date.today().strftime("%Y-%m-%d")
    exp_date = calculate_expiry(st_date, data.duration)
    mem_id = data.member_id or f"ITK-{db.query(Member).count() + 1025}"

    new_member = Member(
        name=data.name,
        email=data.email,
        member_id=mem_id,
        phone=data.phone,
        duration=data.duration,
        start_date=st_date,
        expiry_date=exp_date,
        status="ACTIVE"
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return compute_member_status(new_member)

@app.put("/members/{member_id}")
def update_member(member_id: int, data: MemberInput, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    st_date = data.start_date or member.start_date or date.today().strftime("%Y-%m-%d")
    member.name = data.name
    member.email = data.email
    member.phone = data.phone
    member.duration = data.duration
    member.start_date = st_date
    member.expiry_date = calculate_expiry(st_date, data.duration)
    if data.status:
        member.status = data.status

    db.commit()
    db.refresh(member)
    return compute_member_status(member)

@app.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"message": "Deleted"}