from flask import Flask, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import os
from dotenv import load_dotenv

# Import our custom logic
from models import db, Tenant, User, Transaction, AuditLog, Branch, Customer, Product, ProductVariant, Inventory, Subscription, SuperAdmin
from auth import jwt, requires_role, login_user, get_current_tenant_id, superadmin_login, generate_impersonation_token
from middleware import register_middleware

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)
jwt.init_app(app)

# Register custom middleware (billing lockout, etc.)
register_middleware(app)

# --- STATIC FILE SERVING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'platform_login_page.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.endswith('.html'):
        return send_from_directory(BASE_DIR, path)
    return jsonify({"msg": "Not Found"}), 404

# --- PUBLIC ROUTES ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    print(f"DEBUG: Login attempt for {email}")
    
    # 1. Try regular User login
    token = login_user(email, password)
    
    # 2. If User login fails, try SuperAdmin login
    if not token:
        token = superadmin_login(email, password)
        
    if not token:
        print(f"DEBUG: Login failed for {email}")
        return jsonify({"msg": "Bad credentials"}), 401
    
    print(f"DEBUG: Login successful for {email}")
    return jsonify({"access_token": token}), 200

# --- TENANT SPECIFIC ROUTES (RBAC) ---
@app.route('/pos/transaction', methods=['POST'])
@jwt_required()
@requires_role('Owner', 'Manager', 'Cashier')
def create_transaction():
    tenant_id = get_current_tenant_id()
    data = request.json
    # Logic to record transaction and update inventory
    new_transaction = Transaction(
        tenant_id=tenant_id,
        user_id=get_jwt_identity(),
        branch_id=data.get('branch_id'),
        customer_id=data.get('customer_id'),
        total_amount=data.get('total_amount'),
        payment_method=data.get('payment_method')
    )
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({"msg": "Transaction recorded", "transaction_id": new_transaction.id}), 201

# --- MANAGER OVERRIDE API ---
@app.route('/pos/override', methods=['POST'])
@jwt_required()
@requires_role('Cashier')
def manager_override():
    """Manager Override: An endpoint that accepts a Manager's PIN to authorize restricted actions (refunds, discounts)."""
    tenant_id = get_current_tenant_id()
    data = request.json
    manager_pin = data.get('pin')
    action = data.get('action') # e.g., 'refund', '15_percent_discount'
    
    # Find any user with 'Manager' or 'Owner' role in the same tenant who has this PIN
    manager = User.query.filter_by(tenant_id=tenant_id, pin=manager_pin).filter(User.role.in_(['Manager', 'Owner'])).first()
    
    if not manager:
        return jsonify({"msg": "Invalid Manager PIN"}), 403
    
    # Authorize the action and log it
    audit_log = AuditLog(
        tenant_id=tenant_id,
        user_id=manager.id, # Logged against the manager who provided the override
        action=f"Override: {action} (requested by Cashier {get_jwt_identity()})",
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({"msg": "Override successful", "authorized": True, "manager": manager.username}), 200

# --- OFFLINE SYNC SUPPORT ---
@app.route('/sync/bulk', methods=['POST'])
@jwt_required()
def bulk_sync():
    """Bulk-data ingestion endpoint designed to accept background sync payloads from the frontend's offline mode."""
    tenant_id = get_current_tenant_id()
    data = request.json # Payload containing lists of transactions, customer updates, etc.
    
    # Logic to process bulk sync payloads efficiently
    # Often runs in background using Redis/RQ (Redlock) or batch insertion
    try:
        # Example: Simple bulk batch processing for demo
        for sale in data.get('transactions', []):
            transaction = Transaction(
                tenant_id=tenant_id,
                user_id=sale.get('user_id'),
                total_amount=sale.get('total_amount'),
                payment_method=sale.get('payment_method')
            )
            db.session.add(transaction)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Sync failed", "error": str(e)}), 400
        
    return jsonify({"msg": "Sync successful", "records_processed": len(data.get('transactions', []))}), 200

# --- SUPER ADMIN IMPERSONATION ---
@app.route('/admin/impersonate', methods=['POST'])
@jwt_required()
@requires_role('SuperAdmin')
def impersonate():
    """Super Admin Impersonation: Secure method for a Super Admin to generate a temporary, read-only JWT for a tenant."""
    data = request.json
    target_tenant_id = data.get('tenant_id')
    impersonation_token = generate_impersonation_token(target_tenant_id)
    if not impersonation_token:
        return jsonify({"msg": "Impersonation failed"}), 400
    return jsonify({"impersonation_token": impersonation_token}), 200

@app.route('/pos/products', methods=['GET'])
@jwt_required()
def get_products():
    tenant_id = get_current_tenant_id()
    products = Product.query.filter_by(tenant_id=tenant_id).all()
    # Simplified response for demo
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "variants": [{"id": v.id, "size": v.size, "price": v.price} for v in ProductVariant.query.filter_by(product_id=p.id).all()]
    } for p in products]), 200

@app.route('/pos/customers', methods=['GET'])
@jwt_required()
def get_customers():
    tenant_id = get_current_tenant_id()
    customers = Customer.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([{"id": c.id, "name": f"{c.first_name} {c.last_name}", "phone": c.phone} for c in customers]), 200

@app.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@requires_role('Owner', 'Manager')
def get_stats():
    tenant_id = get_current_tenant_id()
    # Simple aggregations
    sales_count = Transaction.query.filter_by(tenant_id=tenant_id).count()
    revenue = db.session.query(db.func.sum(Transaction.total_amount)).filter_by(tenant_id=tenant_id).scalar() or 0
    return jsonify({
        "total_sales": sales_count,
        "total_revenue": revenue,
        "active_branches": Branch.query.filter_by(tenant_id=tenant_id).count()
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Simple setup for demo; use Flask-Migrate in production
    app.run(host='0.0.0.0', port=5003)
