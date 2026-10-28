# Installation Guide

## Requirements

- Windows 10 or later
- Python 3.10+
- MySQL Server
- Git
- VS Code (recommended)

## Step 1: Create a virtual environment

```powershell
cd C:\path\to\SmartInventorySystem
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Step 2: Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Step 3: Start MySQL

- Install MySQL Server.
- Start the MySQL service in Services or from the MySQL command line.
- Open MySQL Workbench and create a connection to your local server.

## Step 4: Create the database

```sql
CREATE DATABASE IF NOT EXISTS smart_inventory;
USE smart_inventory;
```

## Step 5: Load the schema

```sql
SOURCE C:/path/to/SmartInventorySystem/sql/schema.sql;
```

## Step 6: Configure local environment variables

```powershell
$env:SMART_INVENTORY_DB_HOST = "localhost"
$env:SMART_INVENTORY_DB_USER = "root"
$env:SMART_INVENTORY_DB_PASSWORD = "your_mysql_password"
$env:SMART_INVENTORY_DB_NAME = "smart_inventory"
$env:SMART_INVENTORY_DB_PORT = "3306"
```

## Step 7: Run the app

```powershell
python app.py
```
