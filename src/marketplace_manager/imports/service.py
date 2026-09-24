"""Safe CSV/XLSX parsing, validation, import, and export operations."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from zipfile import BadZipFile

from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.products.validation import validate_product_values

PRODUCT_COLUMNS = ["title", "description", "price", "category", "condition", "location", "sku", "status"]
REQUIRED_COLUMNS = ["title", "price", "sku"]
VALID_STATUSES = {"draft", "active", "archived"}
VALID_CONDITIONS = {"new", "used", "refurbished", "for parts"}


@dataclass
class ImportRow:
    row_number: int
    values: dict[str, str]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ImportResult:
    total_records: int
    successful_records: int
    failed_records: int


def _file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "CSV"
    if suffix == ".xlsx":
        return "XLSX"
    raise ValueError("Choose a CSV or XLSX file.")


def read_product_file(path: Path) -> list[ImportRow]:
    """Read a product file without writing anything to the database."""
    file_type = _file_type(path)
    try:
        if file_type == "CSV":
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            frame = pd.read_excel(path, dtype=str, keep_default_na=False)
    except EmptyDataError as error:
        raise ValueError("The file is empty and contains no header row.") from error
    except (OSError, ValueError, ImportError, UnicodeError, ParserError, BadZipFile) as error:
        raise ValueError(f"Could not read {file_type} file: {error}") from error

    frame.columns = [str(column).strip().lower() for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    rows: list[ImportRow] = []
    for index, record in frame.iterrows():
        values = {column: str(record[column]).strip() if column in frame.columns else "" for column in PRODUCT_COLUMNS}
        rows.append(ImportRow(index + 2, values, _validate_row(values)))
    return rows


def _validate_row(values: dict[str, str]) -> str | None:
    if not any(values.values()):
        return "Empty row."
    _, error = validate_product_values(values["title"], values["price"], values["sku"])
    if error:
        return error
    if values["status"].lower() not in VALID_STATUSES:
        return "Status must be draft, active, or archived."
    if values["condition"].lower() not in VALID_CONDITIONS:
        return "Condition must be New, Used, Refurbished, or For parts."
    return None


def validate_import_rows(rows: list[ImportRow], repository: ProductRepository | None = None) -> list[ImportRow]:
    """Apply duplicate checks to parsed rows and return the same preview rows."""
    seen: set[str] = set()
    existing = {product.sku.strip().lower() for product in repository.list_all()} if repository else set()
    for row in rows:
        if row.error:
            continue
        sku = row.values["sku"].strip().lower()
        if sku in seen:
            row.error = "Duplicate SKU in this file."
        elif sku in existing:
            row.error = "SKU already exists in the product database."
        else:
            seen.add(sku)
    return rows


def import_rows(rows: list[ImportRow], repository: ProductRepository) -> ImportResult:
    """Save valid preview rows and return a result; invalid rows are never written."""
    validate_import_rows(rows, repository)
    successful = 0
    for row in rows:
        if row.error:
            continue
        value = row.values
        price, error = validate_product_values(value["title"], value["price"], value["sku"])
        if error or price is None:
            row.error = error or "Invalid price."
            continue
        repository.create(Product(None, value["title"], value["description"], price, value["category"],
                                  value["condition"], value["location"], value["sku"], value["status"].lower()))
        successful += 1
    return ImportResult(len(rows), successful, len(rows) - successful)


def import_valid_rows(rows: list[ImportRow], repository: ProductRepository) -> int:
    """Backward-compatible helper used by the Products page."""
    return import_rows(rows, repository).successful_records


def export_products(path: Path, products: list[Product]) -> None:
    """Export product records using the format selected by the file extension."""
    rows = [{column: getattr(product, column) for column in PRODUCT_COLUMNS} for product in products]
    frame = pd.DataFrame(rows, columns=PRODUCT_COLUMNS)
    file_type = _file_type(path)
    try:
        if file_type == "CSV":
            frame.to_csv(path, index=False)
        else:
            frame.to_excel(path, index=False)
    except (OSError, ValueError) as error:
        raise ValueError(f"Could not write {file_type} file: {error}") from error
