# Online Shopping System - ER Diagram

## Entity Relationship Diagram

```mermaid
erDiagram
    CustomUser ||--o| ShoppingCart : "has one"
    CustomUser ||--o{ Order : "places"
    
    Category ||--o{ Product : "contains"
    
    Product ||--o{ ProductImage : "has many"
    Product ||--o{ CartItem : "added to cart"
    Product ||--o{ OrderItem : "ordered in"
    
    ShoppingCart ||--o{ CartItem : "contains"
    
    Order ||--o{ OrderItem : "contains"
    
    CustomUser {
        int id PK
        string username UK
        string email UK
        string full_name
        text shipping_address
        string password
        datetime date_joined
        boolean is_active
    }
    
    Category {
        int id PK
        string name UK
        text description
        datetime created_at
    }
    
    Product {
        int id PK
        string product_id UK
        string name
        decimal price
        image thumbnail
        text description
        boolean is_active
        int category_id FK
        datetime created_at
        datetime updated_at
    }
    
    ProductImage {
        int id PK
        int product_id FK
        image image
        string alt_text
        boolean is_primary
        int display_order
        datetime created_at
    }
    
    ShoppingCart {
        int id PK
        int customer_id FK
        datetime created_at
        datetime updated_at
    }
    
    CartItem {
        int id PK
        int cart_id FK
        int product_id FK
        int quantity
        datetime added_at
        datetime updated_at
    }
    
    Order {
        int id PK
        string order_number UK
        int customer_id FK
        text shipping_address
        decimal total_amount
        string status
        datetime purchase_date
        datetime updated_at
    }
    
    OrderItem {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal subtotal
        datetime created_at
        datetime updated_at
    }
```

## Entity Descriptions

### CustomUser
- **Primary Key**: id
- **Unique Keys**: username, email
- **Relationships**:
  - One-to-One with ShoppingCart
  - One-to-Many with Order

### Category
- **Primary Key**: id
- **Unique Keys**: name
- **Relationships**:
  - One-to-Many with Product

### Product
- **Primary Key**: id
- **Unique Keys**: product_id
- **Foreign Keys**: category_id → Category
- **Relationships**:
  - Many-to-One with Category
  - One-to-Many with ProductImage
  - One-to-Many with CartItem
  - One-to-Many with OrderItem

### ProductImage
- **Primary Key**: id
- **Foreign Keys**: product_id → Product
- **Relationships**:
  - Many-to-One with Product

### ShoppingCart
- **Primary Key**: id
- **Foreign Keys**: customer_id → CustomUser
- **Relationships**:
  - One-to-One with CustomUser
  - One-to-Many with CartItem

### CartItem
- **Primary Key**: id
- **Foreign Keys**: cart_id → ShoppingCart, product_id → Product
- **Unique Constraint**: (cart_id, product_id)
- **Relationships**:
  - Many-to-One with ShoppingCart
  - Many-to-One with Product

### Order
- **Primary Key**: id
- **Unique Keys**: order_number
- **Foreign Keys**: customer_id → CustomUser
- **Relationships**:
  - Many-to-One with CustomUser
  - One-to-Many with OrderItem

### OrderItem
- **Primary Key**: id
- **Foreign Keys**: order_id → Order, product_id → Product
- **Relationships**:
  - Many-to-One with Order
  - Many-to-One with Product

## Relationship Summary

| Relationship | Type | Description |
|-------------|------|-------------|
| CustomUser ↔ ShoppingCart | 1:1 | Each user has one shopping cart |
| CustomUser ↔ Order | 1:N | A user can place multiple orders |
| Category ↔ Product | 1:N | A category contains multiple products |
| Product ↔ ProductImage | 1:N | A product can have multiple images |
| Product ↔ CartItem | 1:N | A product can be in multiple cart items |
| Product ↔ OrderItem | 1:N | A product can be in multiple order items |
| ShoppingCart ↔ CartItem | 1:N | A cart contains multiple cart items |
| Order ↔ OrderItem | 1:N | An order contains multiple order items |
