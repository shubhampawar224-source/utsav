from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.database import engine, get_session
from app.models import Product, User, Sale
from app.auth import is_admin_authenticated, verify_session_token
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func
import os
import time
import json
import urllib.parse

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def make_context(request: Request, **kwargs):
    """Build template context including logged-in admin user info."""
    admin_name = None
    initials = "AD"
    avatar_url = None
    token = request.cookies.get("session")
    if token:
        try:
            data = verify_session_token(token)
        except Exception:
            data = None
        if data:
            # data is a dict with possible keys: user, display_name, avatar_url
            admin_name = data.get("display_name") or data.get("user")
            avatar_url = data.get("avatar_url")
    if admin_name:
        parts = admin_name.split()
        initials = ''.join([p[0].upper() for p in parts if p])[:2]
    return dict(request=request, admin_user={"username": admin_name, "initials": initials, "avatar_url": avatar_url}, **kwargs)

# uploads directory for admin product images
UPLOAD_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads'))
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/admin/manage")
def admin_dashboard(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    # summary stats
    with Session(engine) as session:
        # Use SQL COUNT via ORM for efficiency on larger tables
        total_products = session.exec(select(func.count()).select_from(Product)).one()
        total_users = session.exec(select(func.count()).select_from(User)).one()
        total_sales = session.exec(select(func.count()).select_from(Sale)).one()
        recent_sales_raw = session.exec(select(Sale).order_by(Sale.created_at.desc()).limit(12)).all()
        # enrich recent sales with product and user
        recent_sales = []
        for s in recent_sales_raw:
            product = session.get(Product, s.product_id)
            user = session.get(User, s.user_id)
            recent_sales.append({"sale": s, "product": product, "user": user})

        # build chart data for last 7 days
        today = datetime.utcnow().date()
        labels = []
        values = []
        totals_by_date = {}
        start = today - timedelta(days=6)
        for i in range(7):
            d = start + timedelta(days=i)
            totals_by_date[d.isoformat()] = 0.0
        all_sales = session.exec(select(Sale).where(Sale.created_at >= start)).all()
        for s in all_sales:
            key = s.created_at.date().isoformat()
            if key in totals_by_date:
                totals_by_date[key] += float(s.total_price or 0.0)
        for k, v in totals_by_date.items():
            labels.append(k)
            values.append(round(v, 2))

        # latest products for dashboard (show recent products separate from sales)
        latest_raw = session.exec(select(Product).order_by(Product.created_at.desc()).limit(12)).all()
        latest_products = []
        for prod in latest_raw:
            if prod.image_filename:
                image_url = f"/static/uploads/{prod.image_filename}"
            else:
                image_url = f"https://via.placeholder.com/160x120?text={urllib.parse.quote_plus(prod.name)}"
            created = prod.created_at.strftime('%Y-%m-%d') if getattr(prod, 'created_at', None) else ''
            latest_products.append({"product": prod, "image_url": image_url, "created": created})

    chart_data = json.dumps({"labels": labels, "values": values})
    return templates.TemplateResponse("admin/dashboard.html", make_context(request, total_products=total_products, total_users=total_users, total_sales=total_sales, recent_sales=recent_sales, latest_products=latest_products, chart_data=chart_data))


@router.get("/admin/manage/users")
def admin_users(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    with Session(engine) as session:
        users = session.exec(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse("admin/users.html", make_context(request, users=users))


@router.get("/admin/manage/sales")
def admin_sales(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    with Session(engine) as session:
        sales = session.exec(select(Sale).order_by(Sale.created_at.desc())).all()
        # enrich sales with product and user info
        enriched = []
        for s in sales:
            product = session.get(Product, s.product_id)
            user = session.get(User, s.user_id)
            enriched.append({"sale": s, "product": product, "user": user})
    return templates.TemplateResponse("admin/sales.html", make_context(request, sales=enriched))


@router.get("/admin/manage/sales/create")
def sale_create_get(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        users = session.exec(select(User)).all()
    return templates.TemplateResponse("admin/sale_form.html", make_context(request, products=products, users=users))


@router.post("/admin/manage/sales/create")
def sale_create_post(request: Request, product_id: int = Form(...), user_id: int = Form(...), quantity: int = Form(1), session: Session = Depends(get_session)):
    # create a sale record
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    prod = session.get(Product, product_id)
    usr = session.get(User, user_id)
    if not prod or not usr:
        return RedirectResponse(url="/admin/manage/sales")
    total = round(float(prod.price) * int(quantity), 2)
    sale = Sale(product_id=product_id, user_id=user_id, quantity=quantity, total_price=total, status="completed")
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return RedirectResponse(url="/admin/manage/sales", status_code=303)


@router.get("/admin/manage/products")
def admin_products(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    with Session(engine) as session:
        products = session.exec(select(Product).order_by(Product.id.desc())).all()
    return templates.TemplateResponse("admin/products.html", make_context(request, products=products))


@router.get("/admin/manage/products/create")
def product_create_get(request: Request):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse("admin/product_form.html", make_context(request, product=None))


@router.post("/admin/manage/products/create")
async def product_create_post(request: Request, name: str = Form(...), price: float = Form(...), description: str = Form(""), category: str = Form(""), image: UploadFile = File(None), session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    filename = None
    if image:
        filename = f"{int(time.time())}_{os.path.basename(image.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, 'wb') as f:
            content = await image.read()
            f.write(content)
    product = Product(name=name, price=price, description=description, category=category, image_filename=filename)
    session.add(product)
    session.commit()
    session.refresh(product)
    return RedirectResponse(url="/admin/manage/products", status_code=303)


@router.get("/admin/manage/products/edit/{product_id}")
def product_edit_get(request: Request, product_id: int):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            return RedirectResponse(url="/admin/manage/products")
    return templates.TemplateResponse("admin/product_form.html", make_context(request, product=product))


@router.post("/admin/manage/products/edit/{product_id}")
async def product_edit_post(request: Request, product_id: int, name: str = Form(...), price: float = Form(...), description: str = Form(""), category: str = Form(""), image: UploadFile = File(None), session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/admin/manage/products")
    product.name = name
    product.price = price
    product.description = description
    product.category = category
    if image:
        # remove old image
        if product.image_filename:
            old = os.path.join(UPLOAD_DIR, product.image_filename)
            try:
                if os.path.exists(old):
                    os.remove(old)
            except Exception:
                pass
        filename = f"{int(time.time())}_{os.path.basename(image.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, 'wb') as f:
            content = await image.read()
            f.write(content)
        product.image_filename = filename
    session.add(product)
    session.commit()
    session.refresh(product)
    return RedirectResponse(url="/admin/manage/products", status_code=303)


@router.post("/admin/manage/products/delete/{product_id}")
def product_delete(request: Request, product_id: int, session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login")
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/admin/manage/products")
    # delete image file if exists
    if product.image_filename:
        path = os.path.join(UPLOAD_DIR, product.image_filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    session.delete(product)
    session.commit()
    return RedirectResponse(url="/admin/manage/products", status_code=303)
