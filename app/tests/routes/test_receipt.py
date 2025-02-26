import pytest
from fastapi import HTTPException
from datetime import datetime
from sqlmodel import Session
from app.models import Receipt, Product, ProductToReceipt, PaymentType, QuantityType
from app.routes.receipt import get_formatted_receipt
from unittest.mock import MagicMock


async def test_get_formatted_receipt():
    # Mock session and receipt
    mock_session = MagicMock(spec=Session)
    mock_receipt = Receipt(
        id=1,
        user_id=1,
        created_at=datetime(2023, 1, 1, 12, 0),
        payment_type=PaymentType("cash"),
        amount=100,
        shop_name="ФОП Джонсонюк Борис"
    )
    mock_session.get.return_value = mock_receipt

    # Mock products
    mock_products = [
        (
            Product(id=1, name="Test Product 1", price=25.50, quantity_type=QuantityType.ITEMS),
            ProductToReceipt(receipt_id=1, product_id=1, count=2),
        ),
        (
            Product(id=2, name="Test Product 2", price=15.75, quantity_type=QuantityType.ITEMS),
            ProductToReceipt(receipt_id=1, product_id=2, count=1),
        ),
    ]
    mock_session.exec.return_value.all.return_value = mock_products

    result = await get_formatted_receipt(receipt_id=1, session=mock_session)

    expected_lines = [
        "      ФОП Джонсонюк Борис       ",
        "================================",
        "2.00 x 25.50                    ",
        "Test Product 1             51.00",
        "--------------------------------",
        "1.00 x 15.75                    ",
        "Test Product 2             15.75",
        "================================",
        "СУМА                       66.75",
        "cash                      100.00",
        "Решта                      33.25",
        "================================",
        "        01.01.2023 12:00        ",
        "      Дякуємо за покупку!       "
    ]
    expected_output = "\n".join(expected_lines)
    print(result)
    

    assert result == expected_output


async def test_get_formatted_receipt_not_found():
    mock_session = MagicMock(spec=Session)
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_formatted_receipt(receipt_id=999, session=mock_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Receipt not found"
