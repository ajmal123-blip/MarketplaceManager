from pathlib import Path

from PIL import Image

from marketplace_manager.database.image_repository import ImageRepository
from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.images.service import organize_image, process_image, validate_image


def test_image_validation_and_processing(monkeypatch):
    test_dir = Path("data") / "test_images"
    test_dir.mkdir(parents=True, exist_ok=True)
    source = test_dir / "source.png"
    Image.new("RGB", (100, 50), "red").save(source)
    assert validate_image(source) == (True, None)
    assert validate_image(test_dir / "missing.png")[0] is False

    import marketplace_manager.images.service as service

    monkeypatch.setattr(service, "DATA_DIR", test_dir / "organized")
    destination = organize_image(source, 1, 50)
    with Image.open(destination) as result:
        assert max(result.size) <= 50

    processed = process_image(destination, "resize", max_size=25)
    with Image.open(processed) as result:
        assert max(result.size) <= 25

    destination.unlink(); source.unlink(); processed.unlink(); destination.parent.rmdir(); destination.parent.parent.rmdir(); destination.parent.parent.parent.rmdir(); test_dir.rmdir()


def test_image_repository_tracks_product_relationships_and_order() -> None:
    connection = initialize_database(":memory:")
    products = ProductRepository(connection)
    images = ImageRepository(connection)

    product = products.create(Product(None, "Desk lamp", "Warm light", 25.0, "Home", "New", "Karachi", "LAMP-1", "draft"))
    first = images.add(product.id, "/tmp/first.jpg", "first.jpg")
    second = images.add(product.id, "/tmp/second.jpg", "second.jpg")

    assert [image.original_name for image in images.list_for_product(product.id)] == ["first.jpg", "second.jpg"]
    images.move(second.id, -1)
    assert [image.original_name for image in images.list_for_product(product.id)] == ["second.jpg", "first.jpg"]
    assert images.delete(first.id) is True
    assert images.list_for_product(product.id)[0].id == second.id

    connection.close()


def test_process_image_handles_invalid_file_gracefully() -> None:
    bad_file = Path("data") / "invalid_image.png"
    bad_file.write_bytes(b"not-a-real-image")
    try:
        result = process_image(bad_file, "resize")
        assert result is None
    finally:
        if bad_file.exists():
            bad_file.unlink()
