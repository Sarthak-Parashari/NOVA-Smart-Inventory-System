# Database Guide

## Database name

The application expects the database to be named `smart_inventory` unless overridden by `SMART_INVENTORY_DB_NAME`.

## Tables used by the app

### Products

The app reads and writes inventory rows using `Products`.

Required logical fields:

- `product_id`
- `product_name`
- `category`
- `purchase_price`
- `selling_price`
- `stock_quantity`
- `reorder_level`

### Sales

This table stores a sales header.

Required logical fields:

- `sale_id`
- `sale_date`
- `customer_name`
- `total_amount`

### Sale_Items

This is the sales line-item table.

Required logical fields:

- `sale_item_id`
- `sale_id`
- `product_id`
- `quantity`
- `selling_price`
- `purchase_price`

## MySQL Workbench workflow

1. Open MySQL Workbench.
2. Create or open a local connection.
3. Open a SQL tab.
4. Run the schema file: `sql/schema.sql`.
5. Confirm the tables exist with:

```sql
SHOW TABLES;
DESCRIBE Products;
DESCRIBE Sales;
DESCRIBE Sale_Items;
```

## Important notes

- Do not overwrite live production data.
- Never commit actual database dumps, backups, or customer records.
- Review the schema against the application before deploying to a production database.
- Use environment variables for credentials instead of storing them in source files.
