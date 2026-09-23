from pathlib import Path
from PIL import Image
from marketplace_manager.images.service import organize_image, validate_image

def test_image_validation_and_processing(monkeypatch):
    test_dir=Path("data") / "test_images"; test_dir.mkdir(parents=True, exist_ok=True)
    source=test_dir / "source.png"; Image.new("RGB",(100,50),"red").save(source)
    assert validate_image(source) == (True, None)
    assert validate_image(test_dir / "missing.png")[0] is False
    import marketplace_manager.images.service as service
    monkeypatch.setattr(service,"DATA_DIR",test_dir / "organized")
    destination=organize_image(source,1,50)
    with Image.open(destination) as result: assert max(result.size) <= 50
    destination.unlink(); source.unlink(); destination.parent.rmdir(); destination.parent.parent.rmdir(); destination.parent.parent.parent.rmdir(); test_dir.rmdir()
