from app import app, db
from models import Tenant, Subscription, User, Branch, Product, ProductVariant, Inventory, Customer, Transaction, SuperAdmin
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def force_seed():
    with app.app_context():
        print("Clearing database...")
        db.drop_all()
        db.create_all()

        # 1. Subscriptions
        starter = Subscription(name='Starter', price=50.0, features={"users": 2, "branches": 1})
        growth = Subscription(name='Growth', price=150.0, features={"users": 5, "branches": 3})
        pro = Subscription(name='Pro', price=500.0, features={"users": 20, "branches": 10})
        db.session.add_all([starter, growth, pro])
        db.session.commit()

        # 2. Tenants
        metropolis = Tenant(name='Metropolis Urban Planning', domain='metropolis.pos.com', subscription_id=pro.id, billing_status='active')
        db.session.add(metropolis)
        db.session.commit()

        # 3. Super Admin
        sa = SuperAdmin(email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(sa)

        # 4. Users for Metropolis
        branch1 = Branch(tenant_id=metropolis.id, name='Accra Central Branch', location='High Street, Accra')
        db.session.add(branch1)
        db.session.commit()

        # Cashier
        cashier = User(
            tenant_id=metropolis.id, 
            email='cashier@metropolis.com', 
            username='metropolis_cashier', 
            password_hash=generate_password_hash('password123'), 
            role='Cashier', 
            branch_id=branch1.id
        )
        
        # Owner
        owner = User(
            tenant_id=metropolis.id, 
            email='owner@metropolis.com', 
            username='metropolis_owner', 
            password_hash=generate_password_hash('password123'), 
            role='Owner', 
            branch_id=branch1.id
        )
        
        db.session.add_all([owner, cashier])
        db.session.commit()
        
        print("\n--- SEED COMPLETE ---")
        print("Super Admin: admin@example.com / admin123")
        print("Cashier: cashier@metropolis.com / password123")
        print("Owner: owner@metropolis.com / password123")

if __name__ == '__main__':
    force_seed()
