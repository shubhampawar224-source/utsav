from app.database import engine
from sqlmodel import Session, select
from app.models import User, Sale, Product

with Session(engine) as session:
    users = session.exec(select(User)).all()
    sales = session.exec(select(Sale)).all()
    products = session.exec(select(Product)).all()
    print(f"Users: {len(users)}")
    print(f"Products: {len(products)}")
    print(f"Sales: {len(sales)}")
    if users:
        print('Sample user:', users[0].name, users[0].email)
    if sales:
        print('Sample sale total:', sales[0].total_price, 'product_id', sales[0].product_id)
