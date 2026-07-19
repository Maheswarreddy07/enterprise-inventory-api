from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

from database import get_db, MedicineModel, CustomerModel, SupplierModel, SettingModel
from schemas import SettingsUpdate

app = FastAPI(title="Enterprise Inventory Management API System")



@app.get("/api/search", tags=["Search"])
def global_search(q: str, db: Session = Depends(get_db)):
    if not q or len(q.strip()) == 0:
        raise HTTPException(status_code=400, detail="Search query parameter context is required.")
    
    search_term = f"%{q.strip()}%"
    
    medicines = db.query(MedicineModel).filter(
        (MedicineModel.name.like(search_term)) | (MedicineModel.batch.like(search_term))
    ).all()
    
    customers = db.query(CustomerModel).filter(
        (CustomerModel.name.like(search_term)) | (CustomerModel.phone.like(search_term)) | (CustomerModel.email.like(search_term))
    ).all()
    
    suppliers = db.query(SupplierModel).filter(
        (SupplierModel.name.like(search_term)) | (SupplierModel.gstin.like(search_term))
    ).all()
    
    return {
        "query": q,
        "results": {
            "medicines": medicines,
            "customers": customers,
            "suppliers": suppliers
        }
    }



def bulk_csv_importer(file: UploadFile, required_fields: set):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid extension asset context. File must be CSV format.")
    try:
        contents = file.file.read()
        df = pd.read_csv(BytesIO(contents))
        if not required_fields.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Data headers error. Missing columns: {required_fields - set(df.columns)}")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processor parser failure: {str(e)}")


@app.post("/api/import/medicines", tags=["Import"])
def import_medicines(file: UploadFile = File(...), db: Session = Depends(get_db)):
    records = bulk_csv_importer(file, {"name", "batch", "stock"})
    for row in records:
        db.add(MedicineModel(name=row['name'], batch=str(row['batch']), stock=int(row['stock'])))
    db.commit()
    return {"status": "Success", "message": f"Successfully imported {len(records)} medicine records."}


@app.post("/api/import/customers", tags=["Import"])
def import_customers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    records = bulk_csv_importer(file, {"name", "phone", "email"})
    for row in records:
        if not db.query(CustomerModel).filter(CustomerModel.email == row['email']).first():
            db.add(CustomerModel(name=row['name'], phone=str(row['phone']), email=row['email']))
    db.commit()
    return {"status": "Success", "message": f"Successfully processed and imported customer records."}


@app.get("/api/export/{entity}", tags=["Export"])
def export_tabular_data(entity: str, format: str, db: Session = Depends(get_db)):
    model_map = {"medicines": MedicineModel, "customers": CustomerModel, "suppliers": SupplierModel}
    if entity not in model_map:
        raise HTTPException(status_code=404, detail="Requested entity does not exist.")
    
    records = db.query(model_map[entity]).all()
    data_list = [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in records]
    df = pd.DataFrame(data_list)
    
    file_path = f"export_{entity}.{format}"
    
    if format == "csv":
        df.to_csv(file_path, index=False)
        return FileResponse(file_path, media_type="text/csv", filename=file_path)
    elif format == "xlsx":
        df.to_excel(file_path, index=False, engine='openpyxl')
        return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_path)
    else:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'xlsx'")


@app.get("/api/export/{entity}/pdf", tags=["Export"])
def export_pdf_report(entity: str, db: Session = Depends(get_db)):
    model_map = {"medicines": MedicineModel, "customers": CustomerModel, "suppliers": SupplierModel}
    if entity not in model_map:
        raise HTTPException(status_code=404, detail="Target entity path context not found.")
        
    records = db.query(model_map[entity]).all()
    settings = db.query(SettingModel).first()
    file_path = f"report_{entity}.pdf"
    
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"OFFICIAL DATA SUMMARY REPORT: {entity.upper()}")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"Issued By: {settings.company_name} | Layout Profile: {settings.invoice_template}")
    c.drawString(50, 715, f"Hardware Configuration: {settings.printer_settings} | Target Format: {settings.barcode_settings}")
    c.line(50, 705, 550, 705)
    
    y = 675
    c.setFont("Courier", 9)
    for index, row in enumerate(records):
        data_attributes = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        c.drawString(50, y, f"[{index + 1}] -> {str(data_attributes)}")
        y -= 20
        if y < 60:
            c.showPage()
            y = 750
            
    c.save()
    return FileResponse(file_path, media_type="application/pdf", filename=file_path)


@app.get("/api/settings", tags=["Settings"])
def get_system_settings(db: Session = Depends(get_db)):
    return db.query(SettingModel).first()


@app.put("/api/settings", tags=["Settings"])
def update_system_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    settings_row = db.query(SettingModel).first()
    update_intent = payload.dict(exclude_unset=True)
    
    for configuration_key, value in update_intent.items():
        setattr(settings_row, configuration_key, value)
        
    db.commit()
    db.refresh(settings_row)
    return {"status": "Success", "message": "All parameters modified.", "configuration": settings_row}