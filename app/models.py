from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from enum import Enum


class PaymentType(str, Enum):
    CASH = "cash"
    CASHLESS = "cashless"


class QuantityType(str, Enum):
    ITEMS = "items"
    KILOGRAMS = "kilograms"
    LITERS = "liters"


class ProductToReceipt(SQLModel, table=True):
    __tablename__ = "product_to_receipt"

    product_id: int = Field(foreign_key="product.id", primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id", primary_key=True)
    count: int

    # Relationships
    product: "Product" = Relationship(back_populates="receipts")
    receipt: "Receipt" = Relationship(back_populates="products")


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float
    quantity_type: QuantityType = Field(default=QuantityType.ITEMS)

    # Relationships
    receipts: List[ProductToReceipt] = Relationship(back_populates="product")


class Receipt(SQLModel, table=True):
    __tablename__ = "receipt"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payment_type: PaymentType
    amount: float
    shop_name: str

    # Relationships
    products: List[ProductToReceipt] = Relationship(back_populates="receipt")
    user: "User" = Relationship(back_populates="receipts")
    


# For creating/reading products
class ProductCreate(SQLModel):
    name: str
    quantity_type: QuantityType
    quantity: float
    price: float


class ProductRead(ProductCreate):
    id: int


# For creating/reading receipts
class ReceiptCreate(SQLModel):
    payment_type: PaymentType
    amount: float
    shop_name: str
    products: List[ProductCreate]


class ReceiptRead(ReceiptCreate):
    id: int
    created_at: datetime
    user_id: int


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    full_name: Optional[str] = None
    disabled: Optional[bool] = Field(default=False)


class User(UserBase, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    # Relationships
    receipts: List[Receipt] = Relationship(back_populates="user")


# Models for reading/creating data
class UserRead(UserBase):
    id: int


class UserCreate(UserBase):
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None
