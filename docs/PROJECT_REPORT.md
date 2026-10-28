# Project Report

## Overview

NOVA is a compact inventory management application that combines a desktop GUI with a MySQL database. It is designed to help a small business keep track of inventory, customer sales, and profitability with a simple workflow.

## Architecture

The application is split into:

- a Tkinter UI in `app.py`,
- database helper functions in `database.py`,
- MySQL schema definitions in `sql/schema.sql`, and
- documentation and tests in the repository root.

The application follows a layered approach:

1. UI collects user input.
2. `database.py` validates and executes MySQL operations.
3. MySQL stores product and sales data.
4. Result sets are returned to the app for rendering and charts.

## Key business logic

- product stock is validated before sales,
- quantity is reduced atomically during sale recording,
- sales items store historical prices for profit calculations,
- low-stock checks are based on product `stock_quantity` and `reorder_level`,
- revenue and profit are computed from `Sale_Items` and `Products`.

## Observed strengths

- Clear separation between DB logic and UI logic.
- Parameterized SQL queries for core database operations.
- Validation for numeric inputs and stock logic.
- Multi-page dashboard format for inventory operations.

## Risks and caveats

- The database password is expected to be provided by environment variables and must not be committed.
- The exact schema on the local database should be checked against the app's assumptions.
- The desktop app is designed for local use rather than cloud deployment.
