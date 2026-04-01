from app import app, db
from models import Tenant, Branch, Product, ProductVariant, Inventory
import uuid

def seed_products():
    with app.app_context():
        metropolis = Tenant.query.filter_by(name='Metropolis Urban Planning').first()
        branch1 = Branch.query.filter_by(name='Accra Central Branch').first()
        
        if not metropolis or not branch1:
            print("Required tenant or branch not found. Run reset_users.py first.")
            return

        print("Seeding sample products for POS...")
        
        # Product 1
        p1 = Product(tenant_id=metropolis.id, name='Signature Chrono', category='Electronics')
        db.session.add(p1)
        db.session.flush()
        v1 = ProductVariant(tenant_id=metropolis.id, product_id=p1.id, price=249.00, sku=f"AI-CH-{str(uuid.uuid4())[:6]}")
        db.session.add(v1)
        db.session.flush()
        
        # Product 2
        p2 = Product(tenant_id=metropolis.id, name='Studio Wireless', category='Audio')
        db.session.add(p2)
        db.session.flush()
        v2 = ProductVariant(tenant_id=metropolis.id, product_id=p2.id, price=399.00, sku=f"AI-AUD-{str(uuid.uuid4())[:6]}")
        db.session.add(v2)
        db.session.flush()
        
        # Product 3
        p3 = Product(tenant_id=metropolis.id, name='Air Runner Pro', category='Footwear')
        db.session.add(p3)
        db.session.flush()
        v3 = ProductVariant(tenant_id=metropolis.id, product_id=p3.id, price=159.00, sku=f"AI-FT-{str(uuid.uuid4())[:6]}")
        db.session.add(v3)
        db.session.flush()
        
        i1 = Inventory(tenant_id=metropolis.id, branch_id=branch1.id, variant_id=v1.id, quantity=15)
        i2 = Inventory(tenant_id=metropolis.id, branch_id=branch1.id, variant_id=v2.id, quantity=30)
        i3 = Inventory(tenant_id=metropolis.id, branch_id=branch1.id, variant_id=v3.id, quantity=8)
        
        db.session.add_all([i1, i2, i3])
        db.session.commit()
        
        print("Successfully seeded 3 products with inventory.")

if __name__ == '__main__':
    seed_products()
