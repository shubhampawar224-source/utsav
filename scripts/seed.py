"""Seed the database with dummy products for categories like RAM, Mouse, Keyboard, SSD."""
from app.database import create_db_and_tables, engine
from sqlmodel import Session, select
from app.models import Product
import os


def seed():
    create_db_and_tables()
    # remove existing products to avoid duplicates
    with Session(engine) as session:
        existing = session.exec(select(Product)).all()
        for e in existing:
            session.delete(e)
        session.commit()

    # map category -> sample image filename in static/uploads
    # use PNG placeholders for images
    img_map = {
        'RAM': 'ram.png',
        'Mouse': 'mouse.png',
        'Keyboard': 'keyboard.png',
        'SSD': 'ssd.png',
        'Motherboard': 'motherboard.png',
        'GPU': 'gpu.png',
    }

    items = [
        Product(name="Corsair Vengeance 16GB", description="DDR4 3200MHz RAM", price=79.99, category="RAM", image_filename=img_map.get('RAM')),
        Product(name="Kingston 8GB", description="DDR4 2400MHz RAM", price=39.99, category="RAM", image_filename=img_map.get('RAM')),
        Product(name="Logitech G502 Mouse", description="Wired gaming mouse", price=49.99, category="Mouse", image_filename=img_map.get('Mouse')),
        Product(name="HP USB Mouse", description="Comfort mouse", price=12.99, category="Mouse", image_filename=img_map.get('Mouse')),
        Product(name="Corsair K55 Keyboard", description="RGB membrane keyboard", price=59.99, category="Keyboard", image_filename=img_map.get('Keyboard')),
        Product(name="HyperX Alloy FPS", description="Mechanical keyboard", price=99.99, category="Keyboard", image_filename=img_map.get('Keyboard')),
        Product(name="Samsung 970 EVO Plus 500GB", description="NVMe SSD", price=79.00, category="SSD", image_filename=img_map.get('SSD')),
        Product(name="Western Digital Blue 1TB", description="SATA SSD", price=89.00, category="SSD", image_filename=img_map.get('SSD')),
        Product(name="ASUS Prime Motherboard", description="AM4 Motherboard", price=129.99, category="Motherboard", image_filename=img_map.get('Motherboard')),
        Product(name="NVIDIA GTX 1660 Super", description="Graphics card", price=229.99, category="GPU", image_filename=img_map.get('GPU')),
    ]

    # ensure uploads directory exists
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    upload_dir = os.path.normpath(upload_dir)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    with Session(engine) as session:
        for it in items:
            session.add(it)
        session.commit()


if __name__ == '__main__':
    seed()
    print('Seeded database with dummy products (with sample images).')
