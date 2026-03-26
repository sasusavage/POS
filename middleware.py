from flask import Flask, g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from datetime import datetime
from models import Tenant

def register_middleware(app):
    """Register custom middlewares for the Flask application."""

    @app.before_request
    def billing_lockout_check():
        """Pre-request check to enforce billing restrictions."""
        # Skip for login, static assets, and billing-related endpoints
        if request.endpoint in ('login', 'billing_status', 'payment_callback'):
            return None
        
        # SuperAdmins can always access
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt()
            if claims.get('is_sa'):
                return None
            
            tenant_id = claims.get('tenant_id')
            if tenant_id:
                tenant = Tenant.query.get(tenant_id)
                if tenant and tenant.billing_status == 'suspended':
                    # Check if grace period has expired
                    if tenant.grace_period_expiry and tenant.grace_period_expiry < datetime.utcnow():
                        return jsonify({"msg": "Forbidden: Billing lockout. Access restricted to payment routes only."}), 403
            
        except Exception as e:
            # Handle unauthorized or malformed JWT errors
            pass
        return None

    @app.after_request
    def add_headers(response):
        """Add global headers for security and caching."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response
