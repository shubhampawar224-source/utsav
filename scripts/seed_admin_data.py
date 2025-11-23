"""Seed sample users and sales for the admin dashboard (non-destructive).
This script will only insert sample users if no users exist yet.
It will create a few sales tied to existing products and spread them over the last 7 days.
"""
from app.database import create_db_and_tables, engine
from sqlmodel import Session, select
from app.models import Product, User, Sale
from datetime import datetime, timedelta
import random


def seed_admin_data():
    create_db_and_tables()
    with Session(engine) as session:
        users_list = session.exec(select(User)).all()
        users_count = len(users_list)
        if users_count > 0:
            print(f"Users already exist ({users_count}), skipping user seed.")
        else:
            sample_users = [
                User(name="Amit Sharma", email="amit@example.com", phone="+91-9876500011"),
                User(name="Priya Rao", email="priya@example.com", phone="+91-9876500022"),
                User(name="Rohan Singh", email="rohan@example.com", phone="+91-9876500033"),
            ]
            for u in sample_users:
                session.add(u)
            session.commit()
            print(f"Inserted {len(sample_users)} sample users.")

        # create sample sales only if none exist
        sales_list = session.exec(select(Sale)).all()
        sales_count = len(sales_list)
        products = session.exec(select(Product)).all()
        users = session.exec(select(User)).all()
        if not products:
            print("No products found in DB — run scripts/seed.py first to add products.")
            return
        if sales_count > 0:
            print(f"Sales already exist ({sales_count}), skipping sales seed.")
            return

        # create a handful of sales across the last 7 days
        now = datetime.utcnow()
        created = 0
        for _ in range(12):
            prod = random.choice(products)
            usr = random.choice(users)
            qty = random.choice([1, 1, 2])
            total = round(float(prod.price) * qty, 2)
            days_ago = random.randint(0, 6)
            created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            sale = Sale(product_id=prod.id, user_id=usr.id, quantity=qty, total_price=total, status="completed", created_at=created_at)
            session.add(sale)
            created += 1
        session.commit()
        print(f"Inserted {created} sample sales.")


if __name__ == '__main__':
    seed_admin_data()
