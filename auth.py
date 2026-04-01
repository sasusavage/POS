from flask import jsonify, request, g
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request, get_jwt
from functools import wraps
from models import User, Tenant, SuperAdmin, db
from werkzeug.security import generate_password_hash, check_password_hash

jwt = JWTManager()

def requires_role(*roles):
    """Decorator to enforce RBAC using JWT identity and roles."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            if user_role not in roles:
                return jsonify({"msg": "Forbidden: Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def get_current_tenant_id():
    """Helper to get the current tenant ID from JWT claims or headers."""
    verify_jwt_in_request()
    claims = get_jwt()
    return claims.get('tenant_id')

def login_user(email, password):
    """Authenticate a User (within a tenant) and return a JWT."""
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"DEBUG: User not found for {email}")
        return None
    
    if not check_password_hash(user.password_hash, password):
        print(f"DEBUG: Password mismatch for {email}")
        return None
    
    tenant = Tenant.query.get(user.tenant_id)
    if tenant and (tenant.billing_status == 'suspended'):
        # Allow login but restricted access will be handled by middleware
        pass

    additional_claims = {
        "role": user.role,
        "tenant_id": user.tenant_id,
        "branch_id": user.branch_id
    }
    
    access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
    return access_token

def superadmin_login(email, password):
    """Authenticate a SuperAdmin and return a JWT."""
    sa = SuperAdmin.query.filter_by(email=email).first()
    if not sa:
        print(f"DEBUG: SuperAdmin not found for {email}")
        return None
        
    if not check_password_hash(sa.password_hash, password):
        print(f"DEBUG: SuperAdmin password mismatch for {email}")
        return None
    
    additional_claims = {
        "role": "SuperAdmin",
        "is_sa": True
    }
    access_token = create_access_token(identity=sa.id, additional_claims=additional_claims)
    return access_token

def generate_impersonation_token(tenant_id):
    """SuperAdmin generates a temporary, read-only token for a tenant view."""
    verify_jwt_in_request()
    if not get_jwt().get('is_sa'):
        return None
    
    additional_claims = {
        "role": "SuperAdmin_Impersonator",
        "tenant_id": tenant_id,
        "is_read_only": True
    }
    # Temporary short-lived token
    import datetime
    impersonation_token = create_access_token(
        identity="impersonator", 
        additional_claims=additional_claims, 
        expires_delta=datetime.timedelta(hours=1)
    )
    return impersonation_token
