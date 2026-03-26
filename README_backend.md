# POS SaaS Backend (Multi-tenant)

This is a comprehensive Flask-based backend for a multi-tenant Point of Sale & Management SaaS tailored for the Ghana market.

## Features
- **Multi-tenancy**: Data isolation using `tenant_id` foreign keys on all tenant-level tables.
- **RBAC**: Role-based access control with `requires_role` decorator (Owner, Manager, Cashier, Super Admin).
- **Billing Lockout**: Middleware to restrict access for suspended tenants (grace period support).
- **Security**: Manager PIN overrides for sensitive POS actions and JWT-based authentication.
- **Offline Sync**: Bulk-data ingestion endpoint for synchronizing data from the frontend's offline mode.
- **Super Admin Impersonation**: Secure method for Super Admins to view tenant dashboards.
- **Ghanaian Payment Gateways**: Ready integration for Paystack, Flutterwave, and MoMo (via environment variables).

## Project Structure
- `app.py`: Main application entry point and endpoints.
- `models.py`: SQLAlchemy models with multi-tenant data isolation.
- `auth.py`: JWT authentication, RBAC, and impersonation logic.
- `middleware.py`: Global request/response middleware for billing checks.
- `.env.example`: Template for environment variables.
- `requirements.txt`: Python dependencies.

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    - Copy `.env.example` to `.env`.
    - Update `DATABASE_URL` with your PostgreSQL connection string.
    - Set secret keys and payment gateway credentials.

5.  **Initialize Database**:
    - Running `app.py` directly for the first time will create all tables automatically (`db.create_all()`). For production, use `flask db migrate` and `flask db upgrade`.

6.  **Run the Application**:
    ```bash
    flask run --host=0.0.0.0 --port=5000
    ```

## Example API Usage

- **Login**: `POST /login` with `{"email": "...", "password": "..."}`
- **POS Override**: `POST /pos/override` with `{"pin": "1234", "action": "refund"}`
- **Bulk Sync**: `POST /sync/bulk` with transaction payload.
- **Super Admin Impersonation**: `POST /admin/impersonate` with `{"tenant_id": "uuid-here"}`

---
Designed for the Architectural Intelligence & Metropolis Urban Planning workspaces.
