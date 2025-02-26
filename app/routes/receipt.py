from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from ..models import (
    Receipt,
    ReceiptCreate,
    ReceiptRead,
    User,
    ProductToReceipt,
    Product,
)
from ..core.security import get_current_active_user
from ..db.database import get_session

router = APIRouter(prefix="/receipts", tags=["receipts"])

"""
FastAPI router for managing receipts.

This module provides endpoints for CRUD operations on receipts, including:
- Creating new receipts with products
- Reading receipts with filtering options
- Getting formatted receipt output
- Deleting receipts

The router handles authentication and authorization using FastAPI dependencies.
All endpoints require a logged in user except for the public receipt endpoint.

Routes:
    POST /receipts/ : Create a new receipt
    GET /receipts/ : List receipts with optional filters
    GET /receipts/{receipt_id} : Get a specific receipt
    GET /receipts/public/{receipt_id} : Get formatted receipt text
    DELETE /receipts/{receipt_id} : Delete a receipt

Models:
    Receipt: Main receipt model
    Product: Product model
    ProductToReceipt: Association model between receipts and products
    User: User model for authentication

Dependencies:
    get_current_active_user: Validates authenticated user
    get_session: Provides database session
"""

def format_receipt_response(db_receipt: Receipt, session: Session) -> dict:
    # Get products for this receipt
    products = session.exec(
        select(Product, ProductToReceipt)
        .join(ProductToReceipt, Product.id == ProductToReceipt.product_id)
        .where(ProductToReceipt.receipt_id == db_receipt.id)
    ).all()

    # Calculate total and format response
    total = sum(product.price * ptr.count for product, ptr in products)

    return {
        "id": db_receipt.id,
        "products": [
            {
                "name": product.name,
                "price": product.price,
                "quantity": ptr.count,
                "total": product.price * ptr.count,
            }
            for product, ptr in products
        ],
        "payment": {"type": db_receipt.payment_type.value, "amount": db_receipt.amount},
        "total": total,
        "rest": db_receipt.amount - total,
        "created_at": db_receipt.created_at,
    }


@router.post("/", response_model=ReceiptRead)
async def create_receipt(
    receipt_data: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    products_data = receipt_data.products

    db_receipt = Receipt(
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        payment_type=receipt_data.payment_type,
        amount=receipt_data.amount,
        shop_name=receipt_data.shop_name,
    )
    session.add(db_receipt)
    session.commit()
    session.refresh(db_receipt)

    for product_data in products_data:
        product = Product(
            name=product_data.name,
            price=product_data.price,
            quantity=product_data.quantity,
            quantity_type=product_data.quantity_type,
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        receipt_product = ProductToReceipt(
            receipt_id=db_receipt.id,
            product_id=product.id,
            count=product_data.quantity,
        )
        session.add(receipt_product)

    session.commit()
    session.refresh(db_receipt)

    return format_receipt_response(db_receipt, session)


@router.get("/", response_model=List[ReceiptRead])
async def read_receipts(
    skip: int = 0,
    limit: int = 100,
    created_from: datetime = None,
    created_to: datetime = None,
    min_total: float = None,
    max_total: float = None,
    payment_type: str = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    query = select(Receipt).where(Receipt.user_id == current_user.id)
    
    if created_from:
        query = query.where(Receipt.created_at >= created_from)
    if created_to:
        query = query.where(Receipt.created_at <= created_to)
    if payment_type:
        query = query.where(Receipt.payment_type == payment_type)
        
    receipts = session.exec(query.offset(skip).limit(limit)).all()
    
    # Filter by total after fetching since total is calculated from products
    formatted_receipts = [format_receipt_response(r, session) for r in receipts]
    if min_total is not None:
        formatted_receipts = [r for r in formatted_receipts if r["total"] >= min_total]
    if max_total is not None:
        formatted_receipts = [r for r in formatted_receipts if r["total"] <= max_total]
    
    return formatted_receipts


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def read_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this receipt"
        )
    return format_receipt_response(receipt, session)


@router.get("/public/{receipt_id}", response_model=str)
async def get_formatted_receipt(
    receipt_id: int, session: Session = Depends(get_session)
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    products = session.exec(
        select(Product, ProductToReceipt)
        .join(ProductToReceipt, Product.id == ProductToReceipt.product_id)
        .where(ProductToReceipt.receipt_id == receipt_id)
    ).all()

    RECEIPT_SIZE = 32
    lines = []
    lines.append(f"{receipt.shop_name:^{RECEIPT_SIZE}}")
    lines.append("=" * RECEIPT_SIZE)

    total = 0
    for product, ptr in products:
        subtotal = product.price * ptr.count
        total += subtotal
        qty_line = f"{ptr.count:.2f} x {product.price:.2f}"
        lines.append(f"{qty_line:<{RECEIPT_SIZE}}")
        lines.append(f"{product.name:<{RECEIPT_SIZE - 12}}{subtotal:>12.2f}")
        lines.append("-" * RECEIPT_SIZE)

    lines.pop()
    lines.append("=" * RECEIPT_SIZE)
    lines.append(f"СУМА{total:>{RECEIPT_SIZE - 4}.2f}")
    lines.append(
        f"{receipt.payment_type.value:<{RECEIPT_SIZE - 22}}{receipt.amount:>22.2f}"
    )
    lines.append(f"Решта{(receipt.amount - total):>{RECEIPT_SIZE - 5}.2f}")
    lines.append("=" * RECEIPT_SIZE)
    lines.append(f"{receipt.created_at.strftime('%d.%m.%Y %H:%M'):^{RECEIPT_SIZE}}")
    lines.append(f"{'Дякуємо за покупку!':^{RECEIPT_SIZE}}")

    return "\n".join(lines)


@router.delete("/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this receipt"
        )

    session.delete(receipt)
    session.commit()
    return {"message": "Receipt deleted"}
