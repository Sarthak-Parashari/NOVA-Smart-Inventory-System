# NOVA — Smart Inventory Management System

NOVA is a desktop inventory and sales management application built with Python and Tkinter for a MySQL-backed local workflow. The project is designed for small retail or stock management operations, with dashboards, product management, low-stock alerts, sales recording, and basic profit analytics.

## Problem statement

Small businesses often need a simple, reliable way to manage product stock, track sales, and understand revenue/profit without paying for a large enterprise system. This project provides a lightweight, desktop-first solution that keeps inventory data in MySQL and exposes the business logic through a Tkinter interface.

## Project objectives

- Track inventory products with purchase and selling prices.
- Monitor current stock levels and reorder thresholds.
- Record sales while reducing stock in the same transaction.
- Review sales history and calculate estimated gross profit.
- Display dashboard metrics and inventory analytics for quick decision-making.
- Keep database access configurable via environment variables instead of hardcoded credentials.

## Features implemented

The current codebase includes the following features that are clearly implemented in the application:

- Dashboard with KPI cards for product count, stock units, transaction count, revenue, profit, and low-stock count.
- Product listing and search by product name or category.
- Add product form with validation for price, stock quantity, and reorder level.
- Edit selected product details and save updates.
- Delete a product from the database.
- Record a sale by product ID, customer name, and quantity.
- Automatic stock deduction after a successful sale.
- Sales history table with product, quantity, revenue, and estimated profit information.
- Revenue and profit report by month.
- Analytics dashboard with charts for revenue, profit, best sellers, and low-stock status.
- Low-stock watchlist and reorder alerts.
- SQLite-like local project documentation, but the runtime data is MySQL-backed.

## Technologies used

- Python 3.x
- Tkinter (desktop GUI)
- MySQL Server
- mysql-connector-python
- Matplotlib
- Standard library modules such as `os`, `decimal`, `contextlib`, and `datetime`

## Prerequisites

Before running the project, make sure the following are available on your Windows machine:

- Python 3.10+ (project code was validated with Python 3.13 in this workspace)
- MySQL Server installed and running
- MySQL Workbench or a MySQL client
- Git installed
- VS Code recommended for editing and running the app

## Installation instructions for Windows

1. Open a terminal in the project folder.
2. Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## VS Code setup instructions

1. Open the project folder in VS Code.
2. Select the Python interpreter from `.venv`.
3. If prompted, install the Python extension.
4. Open a terminal in VS Code and use the `Activate.ps1` command above.
5. For MySQL configuration, set environment variables in a terminal session or in a `.env` file that is loaded by your shell.

## Python dependency installation

The project requires the following third-party packages:

```text
matplotlib>=3.8,<4.0
mysql-connector-python>=8.0.33,<9.0
```

These are listed in the repository's `requirements.txt` file.

## MySQL setup instructions

1. Install MySQL Server and start the MySQL service.
2. Open MySQL Workbench or a terminal client.
3. Log in as the root or an administrative MySQL user.
4. Create the database if it does not exist:

```sql
CREATE DATABASE IF NOT EXISTS smart_inventory;
USE smart_inventory;
```

5. Run the schema script from `sql/schema.sql`.
6. Ensure the database user has permission to read, write, insert, update, and delete from the `smart_inventory` database.

## Database creation and initialization instructions

The application expects a MySQL database named `smart_inventory` and the tables `Products`, `Sales`, and `Sale_Items`.

From a MySQL client, run:

```sql
SOURCE sql/schema.sql;
```

If using a MySQL terminal directly:

```bash
mysql -u root -p
SOURCE C:/path/to/SmartInventorySystem/sql/schema.sql;
```

The script is designed to define the required schema for the app and does not insert sample sales or product records. It is safe to run on a new database.

## Environment variable configuration

The application reads connection settings from environment variables. The current implementation looks for:

- `SMART_INVENTORY_DB_HOST` (default: `localhost`)
- `SMART_INVENTORY_DB_USER` (default: `root`)
- `SMART_INVENTORY_DB_PASSWORD` (required)
- `SMART_INVENTORY_DB_NAME` (default: `smart_inventory`)
- `SMART_INVENTORY_DB_PORT` (optional integer, default: `3306`)

Example in PowerShell:

```powershell
$env:SMART_INVENTORY_DB_PASSWORD = "your_mysql_password"
$env:SMART_INVENTORY_DB_HOST = "localhost"
$env:SMART_INVENTORY_DB_USER = "root"
$env:SMART_INVENTORY_DB_NAME = "smart_inventory"
$env:SMART_INVENTORY_DB_PORT = "3306"
```

This project includes a safe example file at `.env.example` with placeholders only.

## How to run the application

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

If your MySQL password is configured in the current shell, the GUI should launch and connect to the database.

## Project folder structure

```text
SmartInventorySystem/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
├── .env.example
├── sql/
│   └── schema.sql
├── docs/
│   ├── INSTALLATION.md
│   ├── DATABASE.md
│   ├── USER_GUIDE.md
│   ├── PROJECT_REPORT.md
│   └── ARCHITECTURE.md
├── tests/
│   ├── __init__.py
│   └── test_database_helpers.py
├── screenshots/
│   └── README.md
└── .github/
    └── README.md
```

## Database schema description

The application queries tables named `Products`, `Sales`, and `Sale_Items`. Based on the code in `database.py`, the expected schema is:

### Products

- `product_id` — primary key, auto-incremented integer
- `product_name` — product display name
- `category` — optional category text
- `purchase_price` — purchase cost as a numeric value
- `selling_price` — sale price as a numeric value
- `stock_quantity` — current stock quantity
- `reorder_level` — minimum stock threshold for alerts

### Sales

- `sale_id` — primary key, auto-incremented integer
- `sale_date` — date/time of sale
- `customer_name` — customer label for the sale
- `total_amount` — total sale value

### Sale_Items

- `sale_item_id` — line-item primary key if used by the schema
- `sale_id` — foreign key to `Sales.sale_id`
- `product_id` — foreign key to `Products.product_id`
- `quantity` — number of units sold
- `selling_price` — unit selling price at time of sale
- `purchase_price` — unit purchase price at time of sale

Important note: the app logic assumes these tables exist and uses them in joins and inserts. The exact column types and indexes were not visible in the project source, so the schema script in `sql/schema.sql` is a compatible, application-driven baseline and should be reviewed against your actual MySQL database before production use.

## Screenshots

This project did not include any existing screenshots in the workspace. To document the application visually, add images to the `screenshots/` folder after running the app on your computer.

Suggested screenshots:

- Dashboard overview
- Product management page
- Add product form
- Sales entry form
- Sales history page
- Revenue and profit report
- Analytics dashboard

Placeholder section:

```text
![Dashboard](./screenshots/dashboard.png)
![Products](./screenshots/products.png)
![Record Sale](./screenshots/sale.png)
![Analytics](./screenshots/analytics.png)
```

## Testing information

This repository includes a small unittest suite for validation logic and mocked database behavior.

Run:

```powershell
python -m unittest discover -s tests -v
```

The project was also syntax-checked with Python compilation during validation in this workspace.

## Known limitations

- The project is a local desktop app, not a web application.
- Real database connectivity requires a running MySQL instance and a valid password in `SMART_INVENTORY_DB_PASSWORD`.
- The source code does not include a full migration system or database creation UI.
- Some schema details are inferred from the code and should be checked against the actual MySQL database in use.
- The app is optimized for a single local user environment rather than multi-user production deployment.

## Future enhancements

- Add authentication and role-based access control.
- Support customer records and supplier management.
- Add CSV export/import features.
- Add restocking workflows and backorder management.
- Add email alerts and automated reorder notifications.
- Add a more complete reporting layer with filters and export options.
- Move configuration to a secure `.env` loader or a config management layer.

## Troubleshooting

### MySQL connection error

Check the following:

- MySQL Server is running.
- `SMART_INVENTORY_DB_PASSWORD` is set correctly.
- The user has access to `smart_inventory`.
- You are using the correct host, user, and port values.

### Module import errors

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Tkinter fails to start

This usually means Python was installed without Tkinter support or the environment is not the correct interpreter. Reinstall Python with Tkinter support or use a system interpreter that includes it.

### Matplotlib or MySQL connector not found

Use the project virtual environment and run:

```powershell
python -m pip install -r requirements.txt
```

## Contribution guidelines

Please review `CONTRIBUTING.md` before submitting changes.

## License information

No license has been selected yet for this project. A license will be added only after you choose one of the standard open-source options, such as MIT, Apache 2.0, GPL, or no license.

## Author information

Author: To be filled by the project owner.

Maintainer: To be filled by the project owner.

Repository: This workspace is prepared for local Git usage and GitHub upload once a remote is configured.
