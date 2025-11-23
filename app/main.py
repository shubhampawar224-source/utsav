import os
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from app.database import create_db_and_tables, get_session
from app.models import Product
from app.auth import create_session_token, verify_session_token, is_admin_authenticated, ADMIN_USER, ADMIN_PASS
from sqlmodel import Session

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Electronics Shop")
create_db_and_tables()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/products")
def api_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    per_page: int = 12,
    session: Session = Depends(get_session),
):
    stmt = select(Product)
    if q:
        stmt = stmt.where((Product.name.contains(q)) | (Product.description.contains(q)))
    if category:
        stmt = stmt.where(Product.category == category)
    total = session.exec(select(Product).from_statement(stmt)).all()
    # naive count
    items = session.exec(stmt.order_by(Product.id.desc()).offset((page - 1) * per_page).limit(per_page)).all()
    results = []
    for p in items:
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "image_url": f"/static/uploads/{p.image_filename}" if p.image_filename else None,
        })
    return {"total": len(total), "page": page, "per_page": per_page, "products": results}


@app.get("/product/{product_id}")
def product_detail(request: Request, product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("product.html", {"request": request, "product": product})


@app.get("/admin/login")
def admin_login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/admin/login")
def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    # simple credential check; recommend env vars in production
    if username == ADMIN_USER and password == ADMIN_PASS:
        token = create_session_token(username)
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("session", token, httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/admin/logout")
def admin_logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session")
    return response


@app.get("/admin")
def admin_page(request: Request, session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    products = session.exec(select(Product).order_by(Product.id.desc())).all()
    return templates.TemplateResponse("admin.html", {"request": request, "products": products})


@app.post("/admin/upload")
async def admin_upload(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    image: UploadFile = File(None),
    session: Session = Depends(get_session),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    filename = None
    if image:
        filename = f"{int(__import__('time').time())}_{os.path.basename(image.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            content = await image.read()
            f.write(content)

    product = Product(name=name, price=price, description=description, category=category, image_filename=filename)
    session.add(product)
    session.commit()
    session.refresh(product)

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/edit/{product_id}")
def admin_edit_get(request: Request, product_id: int, session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("edit_product.html", {"request": request, "product": product})


@app.post("/admin/edit/{product_id}")
async def admin_edit_post(
    request: Request,
    product_id: int,
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    image: UploadFile = File(None),
    session: Session = Depends(get_session),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

    # update fields
    product.name = name
    product.price = price
    product.description = description
    product.category = category

    # handle new image upload
    if image:
        # remove old file if exists
        if product.image_filename:
            old_path = os.path.join(UPLOAD_DIR, product.image_filename)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass
        filename = f"{int(__import__('time').time())}_{os.path.basename(image.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            content = await image.read()
            f.write(content)
        product.image_filename = filename

    session.add(product)
    session.commit()
    session.refresh(product)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/delete/{product_id}")
def admin_delete(product_id: int, request: Request, session: Session = Depends(get_session)):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    product = session.get(Product, product_id)
    if not product:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    # delete image file
    if product.image_filename:
        path = os.path.join(UPLOAD_DIR, product.image_filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    session.delete(product)
    session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
