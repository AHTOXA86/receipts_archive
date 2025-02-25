from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from ..models import (
    Receipt, ReceiptCreate, ReceiptRead,
    User, ProductToReceipt, Product
)
from ..core.security import get_current_active_user
from ..db.database import get_session

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/", response_model=ReceiptRead)
async def create_receipt(
    receipt_data: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    products_data = receipt_data.get("products", [])
    payment_data = receipt_data.get("payment", {})

    if not products_data or not payment_data:
        raise HTTPException(status_code=400, detail="Products and payment information are required")

    db_receipt = Receipt(
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        payment_type=payment_data.get("type"),
        payment_amount=payment_data.get("amount")
    )
    session.add(db_receipt)
    session.commit()
    session.refresh(db_receipt)

    for product_data in products_data:
        product = Product(
            name=product_data["name"],
            price=product_data["price"]
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        receipt_product = ProductToReceipt(
            receipt_id=db_receipt.id,
            product_id=product.id,
            count=product_data["quantity"]
        )
        session.add(receipt_product)

    session.commit()
    session.refresh(db_receipt)
    return db_receipt


@router.get("/", response_model=List[ReceiptRead])
async def read_receipts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    receipts = session.exec(
        select(Receipt)
        .where(Receipt.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return receipts


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def read_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this receipt")
    return receipt


@router.post("/{receipt_id}/products/{product_id}")
async def add_product_to_receipt(
    receipt_id: int,
    product_id: int,
    count: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this receipt")

    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    receipt_product = ProductToReceipt(
        receipt_id=receipt_id,
        product_id=product_id,
        count=count
    )
    session.add(receipt_product)
    session.commit()
    return {"message": "Product added to receipt"}


@router.delete("/{receipt_id}/products/{product_id}")
async def remove_product_from_receipt(
    receipt_id: int,
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this receipt")

    receipt_product = session.exec(
        select(ProductToReceipt)
        .where(ProductToReceipt.receipt_id == receipt_id)
        .where(ProductToReceipt.product_id == product_id)
    ).first()

    if not receipt_product:
        raise HTTPException(status_code=404, detail="Product not found in receipt")

    session.delete(receipt_product)
    session.commit()
    return {"message": "Product removed from receipt"}


@router.delete("/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    receipt = session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this receipt")

    session.delete(receipt)
    session.commit()
    return {"message": "Receipt deleted"} 