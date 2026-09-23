"""Parsing, validation, and export logic kept separate from UI code."""
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.products.validation import validate_product_values

PRODUCT_COLUMNS = ["title", "description", "price", "category", "condition", "location", "sku", "status"]

@dataclass
class ImportRow:
    row_number: int; values: dict[str, str]; error: str | None = None

def read_product_file(path: Path) -> list[ImportRow]:
    if path.suffix.lower() == ".csv": frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    elif path.suffix.lower() == ".xlsx": frame = pd.read_excel(path, dtype=str, keep_default_na=False)
    else: raise ValueError("Choose a CSV or XLSX file.")
    missing = [column for column in PRODUCT_COLUMNS if column not in frame.columns]
    if missing: raise ValueError("Missing required columns: " + ", ".join(missing))
    rows=[]
    for index, record in frame.iterrows():
        values={column: str(record[column]).strip() for column in PRODUCT_COLUMNS}; price,error=validate_product_values(values["title"],values["price"],values["sku"])
        if not error and values["status"] not in {"draft","active","archived"}: error="Status must be draft, active, or archived."
        rows.append(ImportRow(index+2,values,error))
    return rows

def import_valid_rows(rows: list[ImportRow], repository: ProductRepository) -> int:
    count=0
    for row in rows:
        if row.error: continue
        value=row.values; price,_=validate_product_values(value["title"],value["price"],value["sku"])
        repository.create(Product(None,value["title"],value["description"],price or 0,value["category"],value["condition"],value["location"],value["sku"],value["status"])); count+=1
    return count

def export_products(path: Path, products: list[Product]) -> None:
    rows=[{column:getattr(product,column) for column in PRODUCT_COLUMNS} for product in products]
    frame=pd.DataFrame(rows,columns=PRODUCT_COLUMNS)
    if path.suffix.lower()==".csv": frame.to_csv(path,index=False)
    elif path.suffix.lower()==".xlsx": frame.to_excel(path,index=False)
    else: raise ValueError("Export filename must end in .csv or .xlsx.")
