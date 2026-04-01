from app import app, db
from models import User, SuperAdmin, Tenant, Branch
from werkzeug.security import generate_password_hash

def clear_and_seed_users():
    with app.app_context():
        print("Deleting existing users and super admins...")
        # Be careful not to drop tables; just delete the records.
        try:
            db.session.query(User).delete()
            db.session.query(SuperAdmin).delete()
            db.session.commit()
            print("Successfully deleted users and super admins.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during deletion: {e}")
            return
            
        print("Seeding new users...")
        # Get existing tenant and branch to associate if they exist, otherwise create dummy ones
        metropolis = Tenant.query.filter_by(name='Metropolis Urban Planning').first()
        branch1 = Branch.query.first()
        
        if not metropolis:
            print("No tenant 'Metropolis Urban Planning' found, creating one...")
            from models import Subscription
            pro = Subscription.query.filter_by(name='Pro').first()
            if not pro:
                pro = Subscription(name='Pro', price=500.0, features={"users": 20, "branches": 10})
                db.session.add(pro)
                db.session.commit()
                
            metropolis = Tenant(name='Metropolis Urban Planning', domain='metropolis.pos.com', subscription_id=pro.id, billing_status='active')
            db.session.add(metropolis)
            db.session.commit()
            
        if not branch1:
            print("No branch found. Creating one...")
            branch1 = Branch(tenant_id=metropolis.id, name='Accra Central Branch', location='High Street, Accra')
            db.session.add(branch1)
            db.session.commit()
            
        # Super Admin
        sa = SuperAdmin(email='admin@platform.com', password_hash=generate_password_hash('admin123'))
        db.session.add(sa)

        # Cashier
        cashier = User(
            tenant_id=metropolis.id, 
            email='cashier@metropolis.com', 
            username='metropolis_cashier', 
            password_hash=generate_password_hash('cashier123'), 
            role='Cashier', 
            branch_id=branch1.id
        )
        
        # Owner
        owner = User(
            tenant_id=metropolis.id, 
            email='owner@metropolis.com', 
            username='metropolis_owner', 
            password_hash=generate_password_hash('owner123'), 
            role='Owner', 
            branch_id=branch1.id
        )
        
        try:
            db.session.add_all([owner, cashier])
            db.session.commit()
            print("\n--- NEW USERS SEEDED ---")
            print("Super Admin: admin@platform.com / admin123")
            print("Cashier: cashier@metropolis.com / cashier123")
            print("Owner: owner@metropolis.com / owner123")
        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == '__main__':
    clear_and_seed_users()
