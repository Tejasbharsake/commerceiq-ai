# CommerceIQ AI
## API Specification Document (OpenAPI 3.0)

---

## 1. API Overview
This document defines the RESTful API architecture for CommerceIQ AI. The API facilitates communication between the Next.js frontend and the Node.js/Express.js backend, interacting with PostgreSQL and external AI services.

## 2. API Standards
*   **Protocol:** HTTPS only (TLS 1.3).
*   **Format:** `application/json` for requests and responses.
*   **Base URL:** `https://api.commerceiq-ai.com/v1`
*   **Naming Convention:** Nouns, plural, kebab-case (e.g., `/api/v1/product-categories`).

## 3. Authentication & Authorization Strategy
*   **Authentication:** JWT (JSON Web Tokens) passed in the `Authorization: Bearer <token>` header.
*   **Authorization:** Role-Based Access Control (RBAC). Roles include `SuperAdmin`, `Vendor`, `Analyst`, and `Support`.
*   **Refresh Tokens:** HttpOnly cookies used to securely issue new Access Tokens.

## 4-7. Standard Response & Error Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    { "field": "email", "message": "Email format is invalid" }
  ]
}
```

### Standard HTTP Status Codes
*   **200 OK**: Request successful.
*   **201 Created**: Resource successfully created.
*   **400 Bad Request**: Malformed syntax or validation error.
*   **401 Unauthorized**: Missing or invalid token.
*   **403 Forbidden**: Valid token, but lacks required role.
*   **404 Not Found**: Resource does not exist.
*   **409 Conflict**: Duplicate resource (e.g., SKU already exists).
*   **422 Validation Error**: Semantic validation failed.
*   **429 Too Many Requests**: Rate limit exceeded.
*   **500 Internal Server Error**: Unexpected backend failure.

## 8. Rate Limiting Strategy
*   **Global Limit:** 1000 requests per IP per 15 minutes.
*   **AI Endpoints:** 50 requests per Vendor per hour to control API costs.
*   **Implementation:** Express-rate-limit backed by Redis. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`.

## 9-15. Global Strategies
*   **Versioning:** URI versioning (currently `/v1/`).
*   **Pagination:** Offset/Limit standard (`?page=1&limit=20`). Response includes `total`, `page`, `limit`.
*   **Filtering & Sorting:** Query params: `?status=ACTIVE&sort=-createdAt`.
*   **Security Headers:** Helmet.js enforcing CSP, X-Frame-Options, HSTS.
*   **Logging & Auditing:** Winston/Morgan logging all endpoints. `POST/PUT/DELETE` methods auto-logged to PostgreSQL `AuditLogs`.

---

# DETAILED API ENDPOINTS

*(Note: Representative core APIs fully detailed as requested. All 50+ endpoints follow this exact structural schema in the Postman/Swagger collection).*

## AUTHENTICATION APIs

### POST /api/auth/login
1. **Endpoint:** `/api/v1/auth/login`
2. **Description:** Authenticates a user and issues a JWT.
3. **HTTP Method:** POST
4. **Authentication Required:** No
5. **Authorization Required:** None
6. **Request Headers:** `Content-Type: application/json`
7. **Path Parameters:** None
8. **Query Parameters:** None
9. **Request Body:**
    ```json
    {
      "email": "vendor@commerceiq.com",
      "password": "SecurePassword123!"
    }
    ```
10. **Validation Rules:** `email` must be valid format. `password` required.
11. **Success Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Login successful",
      "data": { "token": "eyJhbGciOi...", "user": { "id": "uuid", "role": "Vendor" } }
    }
    ```
12. **Error Response (401 Unauthorized):** `{"success": false, "message": "Invalid credentials"}`
13. **Business Rules:** Account must not be locked or soft-deleted.

---

## PRODUCT MANAGEMENT APIs

### POST /api/products
1. **Endpoint:** `/api/v1/products`
2. **Description:** Creates a new product catalog entry.
3. **HTTP Method:** POST
4. **Authentication Required:** Yes
5. **Authorization Required:** `Vendor`, `SuperAdmin`
6. **Request Headers:** `Authorization: Bearer <token>`
7. **Request Body:**
    ```json
    {
      "title": "Wireless Earbuds",
      "sku": "WE-001",
      "categoryId": "uuid",
      "price": 129.99
    }
    ```
10. **Validation Rules:** `price` > 0. `sku` must be unique per vendor.
11. **Success Response (201 Created):** `{"success": true, "message": "Product created", "data": {"id": "uuid"}}`
12. **Error Response (409 Conflict):** `{"success": false, "message": "SKU already exists"}`
14. **Business Rules:** Vendor can only create products under their assigned `vendor_id`.

---

## INVENTORY MANAGEMENT APIs

### POST /api/inventory/reduce-stock
1. **Endpoint:** `/api/v1/inventory/reduce-stock`
2. **Description:** Deducts stock from inventory (used internally by Order Service).
3. **HTTP Method:** POST
4. **Authentication Required:** Yes
5. **Authorization Required:** `System`, `Vendor`
6. **Request Body:**
    ```json
    {
      "productId": "uuid",
      "warehouseId": "uuid",
      "quantity": 2
    }
    ```
10. **Validation Rules:** `quantity` must be > 0.
12. **Error Response (422 Validation Error):** `{"success": false, "message": "Insufficient stock"}`
14. **Business Rules:** DB transaction requires pessimistic locking (`SELECT FOR UPDATE`).

---

## AI APIs

### POST /api/ai/product-description
1. **Endpoint:** `/api/v1/ai/product-description`
2. **Description:** Generates SEO-optimized descriptions using OpenAI/Gemini.
3. **HTTP Method:** POST
4. **Authentication Required:** Yes
5. **Authorization Required:** `Vendor`
6. **Request Body:**
    ```json
    {
      "productName": "Ergonomic Desk Chair",
      "keyFeatures": ["Lumbar support", "Mesh back", "Adjustable arms"]
    }
    ```
11. **Success Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "AI generation successful",
      "data": { "description": "Experience ultimate comfort with our Ergonomic..." }
    }
    ```
14. **Business Rules:** Rate limited to 50 calls/hour per vendor. Cached in Redis to prevent duplicate generation costs.

---

## OpenAPI 3.0 YAML FORMAT (Sample Structure)

```yaml
openapi: 3.0.0
info:
  title: CommerceIQ AI API
  description: E-Commerce Administration & BI Platform APIs
  version: 1.0.0
servers:
  - url: https://api.commerceiq-ai.com/v1
    description: Production Server
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    SuccessResponse:
      type: object
      properties:
        success:
          type: boolean
          example: true
        message:
          type: string
        data:
          type: object
paths:
  /auth/login:
    post:
      summary: User Login
      tags: [Authentication]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email: { type: string }
                password: { type: string }
      responses:
        '200':
          description: Successful Login
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SuccessResponse'
```

---

## POSTMAN COLLECTION STRUCTURE
*   **CommerceIQ AI API V1** (Collection)
    *   `Environment`: Production / Staging (Variables: `{{baseUrl}}`, `{{token}}`)
    *   **Folder: Authentication** (Login, Register, Refresh)
    *   **Folder: Products** (CRUD, Search, Bulk Upload)
    *   **Folder: Orders** (Place Order, Status Update, History)
    *   **Folder: Inventory** (Add Stock, Alerts)
    *   **Folder: AI Services** (Desc Gen, SEO Gen, Sales Analytics)
    *   **Folder: Vendor Admin** (Dashboard, Reports)

---

## API SECURITY DOCUMENTATION
1.  **JWT Authentication Flow**: Client logs in -> Server issues short-lived JWT & HttpOnly refresh cookie -> Client sends JWT in `Authorization` header.
2.  **Refresh Token Flow**: JWT expires -> Interceptor catches 401 -> Client calls `/api/auth/refresh-token` -> Server validates HttpOnly cookie in DB -> Server issues new JWT.
3.  **CORS Policy**: Strictly limited to verified frontend domains.
4.  **SQL Injection / XSS**: All bodies parsed and sanitized via `zod` before DB ingestion. ORM prevents direct SQL execution.

---
**End of Document**
