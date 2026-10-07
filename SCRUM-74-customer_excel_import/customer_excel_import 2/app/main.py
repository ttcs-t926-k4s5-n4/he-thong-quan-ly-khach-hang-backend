from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import shutil
import os

from . import models, schemas, crud
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Excel Import API")

TEMP_DIR = "/tmp/excel_imports"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/import/template")
def download_template():
    # In a real app, this returns a static .xlsx file
    # For this demo, we assume the file exists in the project folder
    template_path = "templates/customer_template.xlsx"
    return FileResponse(path=template_path, filename="customer_template.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/import/preview", response_model=schemas.ImportPreviewResponse)
async def preview_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        return crud.parse_excel_and_preview(db, file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/import/confirm")
def confirm_import(request: schemas.ImportConfirmRequest, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        count = crud.confirm_import(db, file_path, request.rows)
        return {"message": f"Successfully imported {count} customers."}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
