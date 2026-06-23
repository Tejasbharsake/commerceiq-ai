# CommerceIQ AI
## Database Design Document (DDD)

---

## 1. Database Overview
*   **Database Engine**: PostgreSQL 16+
*   **Architecture**: Multi-Tenant SaaS Architecture
*   **Scale**: 100k+ Products, 50k+ Customers, 10k+ Vendors, 1M+ Orders, 10k+ Daily Trans.
*   **Target Audience**: Database Architects, Backend Developers, DevOps, QA.

## 2. Database Architecture
CommerceIQ AI utilizes a highly normalized (3NF) relational database architecture. Multi-tenancy is logically separated via the `vendor_id` and `tenant_id` columns, ensuring data isolation.

## 3. Database Standards & Naming Conventions
*   **Tables**: Plural `snake_case` (e.g., `product_categories`).
*   **Columns**: Singular `snake_case` (e.g., `user_id`, `created_at`).
*   **Primary Keys**: `id` of type `UUID`.
*   **Foreign Keys**: `[entity]_id` (e.g., `vendor_id`).
*   **Indexes**: `idx_[table]_[column]` (e.g., `idx_users_email`).

## 4. Common Table Standards
Every table includes standard audit columns:
*   `id` (UUID, Primary Key)
*   `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT NOW())
*   `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT NOW())
*   `created_by` (UUID, NULLABLE)
*   `updated_by` (UUID, NULLABLE)
*   `is_active` (BOOLEAN, NOT NULL, DEFAULT TRUE)
*   `is_deleted` (BOOLEAN, NOT NULL, DEFAULT FALSE)

---

## 5. Database Relationship Matrix

| Parent Table | Child Table | Relationship | FK Constraint Column |
| :--- | :--- | :--- | :--- |
| Users | Vendors | 1:1 | `user_id` |
| Users | Customers | 1:1 | `user_id` |
| Roles | Users | 1:M | `role_id` (via `user_roles`) |
| Vendors | Products | 1:M | `vendor_id` |
| Categories | Products | 1:M | `category_id` |
| Products | Inventory | 1:M | `product_id` |
| Customers | Orders | 1:M | `customer_id` |
| Orders | OrderItems | 1:M | `order_id` |
| Products | OrderItems | 1:M | `product_id` |
| Orders | Payments | 1:1 | `order_id` |
| Orders | RefundRequests | 1:M | `order_id` |
| Products | Reviews | 1:M | `product_id` |

---

## 6. SQL Design & Entity Definitions (CREATE TABLE Scripts)

*Note: For brevity, the standard audit columns are explicitly defined in the first table and implicitly assumed to be identical for all subsequent tables in this documentation.*

### 6.1 Authentication Module

```sql
-- Roles Table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by UUID,
    updated_by UUID,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    last_login TIMESTAMPTZ,
    -- Audit columns omitted for brevity...
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);
CREATE INDEX idx_users_email ON users(email);

-- UserRoles Table
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

### 6.2 Vendor & Product Modules

```sql
-- Vendors Table
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    business_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(100) UNIQUE,
    status VARCHAR(50) DEFAULT 'Pending'
    -- Audit columns omitted...
);

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES categories(id),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE
    -- Audit columns omitted...
);

-- Products Table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    category_id UUID NOT NULL REFERENCES categories(id),
    sku VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2) NOT NULL
    -- Audit columns omitted...
);
CREATE INDEX idx_products_vendor ON products(vendor_id);
CREATE INDEX idx_products_sku ON products(sku);
```

### 6.3 Inventory Module

```sql
-- Warehouses Table
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    location TEXT NOT NULL
);

-- Inventory Table
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    quantity INT NOT NULL DEFAULT 0,
    UNIQUE(product_id, warehouse_id)
);

-- InventoryTransactions Table
CREATE TABLE inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id),
    change_qty INT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- e.g., 'SALE', 'RESTOCK'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.4 Order & Payment Modules

```sql
-- Customers Table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

-- Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING'
    -- Audit columns omitted...
);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);

-- OrderItems Table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

-- Payments Table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL UNIQUE REFERENCES orders(id),
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL
);
```

### 6.5 Review & Refund Modules

```sql
-- Reviews Table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT
);

-- RefundRequests Table
CREATE TABLE refund_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'REQUESTED',
    reason TEXT
);
```

### 6.6 AI Module & Audit Logs

```sql
-- AIRequests Table
CREATE TABLE ai_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    service_type VARCHAR(50) NOT NULL, -- e.g., 'DESCRIPTION_GEN'
    prompt_used TEXT,
    response_payload JSONB,
    tokens_consumed INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ai_requests_user ON ai_requests(user_id);

-- AuditLogs Table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_record ON audit_logs(record_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
```

*(Remaining module tables such as Wishlists, VendorDocuments, Notifications follow identical structural paradigms).*

---

## 7. Indexing & Optimization Strategy

### 7.1 PostgreSQL Optimization Strategy
*   **Clustered Indexes:** Not typically used in modern PostgreSQL; instead, `CLUSTER table USING index` can be run periodically during maintenance windows if read-heavy historical queries require physical disk ordering.
*   **Non-Clustered Indexes:** Standard B-Tree indexes applied to all foreign keys to ensure fast `JOIN` performance.
*   **Composite Indexes:** Utilized where multi-column lookups are frequent (e.g., `CREATE INDEX idx_order_items ON order_items(order_id, product_id)`).
*   **Read/Write Optimization:** Use of `JSONB` for `AuditLogs` and `AIResponses` to prevent excessive table joins for unstructured schema data.

### 7.2 Partitioning Strategy
*   **Date-Range Partitioning:** Highly volatile tables (`Orders`, `AuditLogs`, `InventoryTransactions`, `AIRequests`) will be partitioned by `created_at` in monthly segments (e.g., `orders_2026_06`).
*   This prevents index bloat and ensures queries filtering by recent dates are highly optimized.

---

## 8. Security Design
*   **Row Level Security (RLS):** Enabled on tenant-specific tables. E.g., `ALTER TABLE products ENABLE ROW LEVEL SECURITY;` combined with policies ensuring `vendor_id = current_setting('app.current_vendor_id')`.
*   **Data Encryption:** Passwords hashed with `bcrypt`. PostgreSQL volume encrypted at rest via cloud provider KMS.
*   **Sensitive Data Handling:** PII (Personally Identifiable Information) in `customers` table restricted.
*   **Audit Logging:** `AuditLogs` capture all DML operations on sensitive tables for compliance.

---

## 9. Backup & Recovery Strategy
*   **Full Backup:** Logical backups (`pg_dump`) executed daily at 03:00 AM UTC and transferred to an immutable AWS S3 bucket.
*   **Incremental Backup:** Write-Ahead Logging (WAL) archiving enabled continuously using `pgBackRest` or `wal-g`.
*   **Disaster Recovery Plan:** RPO (Recovery Point Objective) is < 5 minutes. RTO (Recovery Time Objective) is < 2 hours via promoting the cross-zone read-replica.

---

## 10. Archival & Data Retention Policy
*   **Active Data:** Orders and transactions from the last 24 months.
*   **Archival:** Orders older than 24 months are moved to an offline analytical data warehouse (e.g., AWS Redshift or Snowflake).
*   **Retention:** Audit Logs and AI Requests are purged after 7 years to comply with standard financial and privacy regulations.

---
**End of Document**
