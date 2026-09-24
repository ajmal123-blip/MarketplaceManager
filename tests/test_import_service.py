from pathlib import Path

import pandas as pd
import pytest

from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.imports.service import (
    PRODUCT_COLUMNS,
    export_products,
    import_rows,
    read_product_file,
    validate_import_rows,
)


def frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Lamp", "Warm light", "10", "Home", "New", "Karachi", "L1", "draft"],
            ["", "", "bad", "", "Unknown", "", "", "bad"],
        ],
        columns=PRODUCT_COLUMNS,
    )


def test_csv_and_xlsx_parsing_and_validation(tmp_path: Path) -> None:
    for suffix in ("csv", "xlsx"):
        path = tmp_path / f"products.{suffix}"
        if suffix == "csv":
            frame().to_csv(path, index=False)
        else:
            frame().to_excel(path, index=False)
        rows = read_product_file(path)
        assert rows[0].error is None
        assert rows[1].error == "Title is required."


def test_import_validates_condition_status_and_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "products.csv"
    pd.DataFrame(
        [
            ["A", "1", "New", "SKU-1", "draft"],
            ["B", "2", "Unknown", "SKU-2", "active"],
            ["C", "3", "Used", "SKU-1", "active"],
        ],
        columns=["title", "price", "condition", "sku", "status"],
    ).to_csv(path, index=False)
    rows = read_product_file(path)
    assert "Condition must be" in rows[1].error
    repository = ProductRepository(initialize_database(":memory:"))
    validate_import_rows(rows, repository)
    assert rows[2].error == "Duplicate SKU in this file."
    result = import_rows(rows, repository)
    assert (result.total_records, result.successful_records, result.failed_records) == (3, 1, 2)
    assert repository.list_all()[0].sku == "SKU-1"


def test_csv_and_xlsx_export(tmp_path: Path) -> None:
    product = Product(None, "Desk lamp", "Warm", 24.99, "Home", "Used", "Karachi", "LAMP-1", "draft")
    for suffix in ("csv", "xlsx"):
        path = tmp_path / f"export.{suffix}"
        export_products(path, [product])
        assert path.exists()
        if suffix == "csv":
            exported = pd.read_csv(path)
        else:
            exported = pd.read_excel(path)
        assert list(exported.columns) == PRODUCT_COLUMNS
        assert exported.iloc[0]["sku"] == "LAMP-1"


def test_empty_and_invalid_files_are_reported_safely(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_product_file(empty)

    missing = tmp_path / "missing.csv"
    missing.write_text("description,category\ntext,Home\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required columns"):
        read_product_file(missing)

    invalid = tmp_path / "invalid.xlsx"
    invalid.write_text("not an excel workbook", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not read XLSX file"):
        read_product_file(invalid)
