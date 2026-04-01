from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

db = SQLAlchemy()

class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Global Tables
class Tenant(Base):
    __tablename__ = 'tenants'
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    currency = db.Column(db.String(10), default='GHS')
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'), nullable=False)
    billing_status = db.Column(db.String(20), default='active')  # active, suspended, grace
    grace_period_expiry = db.Column(db.DateTime, nullable=True)
    subscription = db.relationship('Subscription', backref='tenants')

class Subscription(Base):
    __tablename__ = 'subscriptions'
    name = db.Column(db.String(50), nullable=False)  # Starter, Growth, Pro, Enterprise
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.JSON, nullable=True)

class SuperAdmin(Base):
    __tablename__ = 'super_admins'
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# Tenant Tables - All must have tenant_id for data isolation
class TenantBase(Base):
    __abstract__ = True
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)

class User(TenantBase):
    __tablename__ = 'users'
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Owner, Manager, Cashier
    pin = db.Column(db.String(6), nullable=True) # For manager override
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=True)

class Branch(TenantBase):
    __tablename__ = 'branches'
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=True)

class Product(TenantBase):
    __tablename__ = 'products'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)

class ProductVariant(TenantBase):
    __tablename__ = 'product_variants'
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Float, nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)

class Inventory(TenantBase):
    __tablename__ = 'inventory_levels'
    variant_id = db.Column(db.String(36), db.ForeignKey('product_variants.id'), nullable=False)
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)

class Customer(TenantBase):
    __tablename__ = 'customers'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    loyalty_points = db.Column(db.Integer, default=0)

class Transaction(TenantBase):
    __tablename__ = 'transactions'
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # Cash, Card, MoMo
    status = db.Column(db.String(20), default='completed') # completed, refunded, pending

class TransactionItem(TenantBase):
    __tablename__ = 'transaction_items'
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    variant_id = db.Column(db.String(36), db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)

class AuditLog(TenantBase):
    __tablename__ = 'audit_logs'
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_table = db.Column(db.String(100), nullable=True)
    target_id = db.Column(db.String(36), nullable=True)
