import pandas as pd
from sqlalchemy.orm import Session
from . import models, schemas
from thefuzz import fuzz

def parse_excel_and_preview(db: Session, file_path: str):
    df = pd.read_excel(file_path)

    # Expected columns
    expected_cols = ["name", "tax_id", "website", "phone"]
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Thiếu cột bắt buộc: {col}")

    preview_rows = []
    valid_count = 0
    duplicate_count = 0
    error_count = 0

    for index, row in df.iterrows():
        row_idx = index + 2 # Excel index starts at 1, and there is a header
        name = str(row["name"]) if pd.notnull(row["name"]) else None
        tax_id = str(row["tax_id"]) if pd.notnull(row["tax_id"]) else None
        website = str(row["website"]) if pd.notnull(row["website"]) else None
        phone = str(row["phone"]) if pd.notnull(row["phone"]) else None

        if not name:
            preview_rows.append(schemas.CustomerImportRow(
                row_index=row_idx, name="", tax_id=tax_id, website=website, phone=phone,
                status="error", error_message="Tên khách hàng không được để trống"
            ))
            error_count += 1
            continue

        # Duplicate detection
        existing = db.query(models.Customer).filter(
            (models.Customer.tax_id == tax_id) if tax_id else False
        ).first()

        if not existing and tax_id:
            # Fuzzy match on name as fallback
            all_custs = db.query(models.Customer).all()
            for c in all_custs:
                if fuzz.token_sort_ratio(name, c.name) >= 90:
                    existing = c
                    break

        if existing:
            preview_rows.append(schemas.CustomerImportRow(
                row_index=row_idx, name=name, tax_id=tax_id, website=website, phone=phone,
                status="duplicate", error_message=f"Trùng với khách hàng: {existing.name}",
                existing_id=existing.id
            ))
            duplicate_count += 1
        else:
            preview_rows.append(schemas.CustomerImportRow(
                row_index=row_idx, name=name, tax_id=tax_id, website=website, phone=phone,
                status="valid"
            ))
            valid_count += 1

    return schemas.ImportPreviewResponse(
        total_rows=len(preview_rows),
        valid_rows=valid_count,
        duplicate_rows=duplicate_count,
        error_rows=error_count,
        rows=preview_rows
    )

def confirm_import(db: Session, file_path: str, row_indices: List[int]):
    df = pd.read_excel(file_path)
    imported_count = 0

    for idx in row_indices:
        # Convert row_index back to pandas index (row_index = index + 2)
        df_idx = idx - 2
        if df_idx < 0 or df_idx >= len(df):
            continue

        row = df.iloc[df_idx]
        cust = models.Customer(
            name=str(row["name"]),
            tax_id=str(row["tax_id"]) if pd.notnull(row["tax_id"]) else None,
            website=str(row["website"]) if pd.notnull(row["website"]) else None,
            phone=str(row["phone"]) if pd.notnull(row["phone"]) else None,
        )
        db.add(cust)
        imported_count += 1

    db.commit()
    return imported_count
