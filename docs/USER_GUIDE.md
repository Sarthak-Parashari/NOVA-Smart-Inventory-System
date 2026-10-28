# User Guide

## Launching the application

1. Open PowerShell in the project folder.
2. Activate the virtual environment.
3. Set the MySQL password using `SMART_INVENTORY_DB_PASSWORD`.
4. Run:

```powershell
python app.py
```

## Main navigation

The application includes these sections:

- Dashboard
- Products
- Add Product
- Record Sale
- Sales History
- Revenue & Profit
- Analytics

## Working with products

- Search by product name or category.
- Select a product in the table to edit it.
- Save changes after updating details.
- Delete a product after confirming the row selection.

## Recording sales

- Enter a valid Product ID.
- Provide a customer name or leave it empty for a walk-in customer.
- Enter a quantity greater than zero.
- The app will reject sales that exceed the current stock quantity.

## Analytics

The analytics page uses the current MySQL tables to display charts for:

- revenue by month,
- profit by month,
- best-selling products,
- category stock distribution,
- low-stock products.
