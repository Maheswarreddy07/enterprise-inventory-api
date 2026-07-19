from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./system.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MedicineModel(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    batch = Column(String, index=True, nullable=False)
    stock = Column(Integer, default=0)

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    phone = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

class SupplierModel(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contact = Column(String, nullable=True)
    gstin = Column(String, index=True, nullable=False)

class SettingModel(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, default=1)
    company_name = Column(String, default="Global Enterprise ERP")
    gst_percentage = Column(Float, default=18.0)
    invoice_template = Column(String, default="Standard Clean Layout")
    printer_settings = Column(String, default="Thermal 80mm")
    barcode_settings = Column(String, default="Code128")
    email_smtp_host = Column(String, default="smtp.gmail.com")
    email_smtp_port = Column(Integer, default=587)
    backup_settings = Column(String, default="Daily Auto-Backup")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        if not db.query(SettingModel).first():
            default_settings = SettingModel(id=1)
            db.add(default_settings)
            db.commit()
        yield db
    finally:
        db.close()