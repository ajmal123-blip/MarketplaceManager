from pathlib import Path
import pandas as pd
from marketplace_manager.imports.service import PRODUCT_COLUMNS, read_product_file

def test_csv_and_xlsx_parsing_and_validation():
    folder=Path("data")/"import_tests"; folder.mkdir(parents=True,exist_ok=True)
    frame=pd.DataFrame([["Lamp","", "10","Home","New","Karachi","L1","draft"],["","","bad","","","","","bad"]],columns=PRODUCT_COLUMNS)
    for suffix in ("csv","xlsx"):
        path=folder/f"products.{suffix}"
        if suffix=="csv": frame.to_csv(path,index=False)
        else: frame.to_excel(path,index=False)
        rows=read_product_file(path); assert rows[0].error is None; assert rows[1].error == "Title is required."
        path.unlink()
    folder.rmdir()
