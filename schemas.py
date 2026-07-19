from pydantic import BaseModel, EmailStr
from typing import Optional

class MedicineCreate(BaseModel):
    name: str
    batch: str
    stock: int

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr

class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    gst_percentage: Optional[float] = None
    invoice_template: Optional[str] = None
    printer_settings: Optional[str] = None
    barcode_settings: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    backup_settings: Optional[str] = None

    class Config:
        from_attributes = True