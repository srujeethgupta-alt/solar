# Solar Stock Management System - Project Report

This document provides a comprehensive overview of the Solar Stock Management System, covering its architecture, feature set, file structure, and technical components.

## 1. Project Architecture & Technology Stack

The application is built as a single-page application (SPA) with a lightweight Python backend. It is designed to be fully self-contained, running without a traditional database engine.

- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Custom Solar Theme with Glassmorphism)
- **Backend Framework**: Python with FastAPI (for high performance and easy API routing)
- **Data Storage**: Local JSON file (`data/stock.json`) protected by thread locks for concurrency safety. No SQL/NoSQL databases are used.
- **Reporting**: 
  - `reportlab` (for generating PDF reports)
  - `openpyxl` (for generating Excel `.xlsx` reports)
- **Automations**: 
  - `APScheduler` (for scheduling daily background tasks)
  - Meta Business Cloud API (for sending automated WhatsApp summary reports)
- **Data Visualization**: Chart.js (for rendering Dashboard analytics)
- **Iconography**: Lucide Icons

---

## 2. Core Features

### 🔐 Security & Authentication
- **Admin Login**: A single secure admin entry point (`admin` / `solar123`).
- **Session Management**: JWT-like token authentication. The frontend stores tokens in `localStorage` and passes them in the `Authorization` header for all protected API calls.

### 📊 Interactive Dashboard
- **Live Metrics**: Total Products, Available Stock, Low Stock Warnings, Out of Stock, Today's Inflow, and Today's Outflow.
- **Visual Analytics**: 
  - Stock Activity Trend Chart (Bar chart mapping last 7 days of IN vs OUT operations).
  - Category Distribution Chart (Doughnut chart mapping inventory across Solar Panels, Inverters, Batteries, etc.).

### 📦 Product Management (Catalog)
- **Dynamic Stock Summary**: Visual progress bars showing stock levels per product type (auto-calculates max stock to scale bars), specifically highlighting Solar Panels and Inverters.
- **CRUD Operations**: Add, Edit, and Delete product entries.
- **Granular Details**: Tracks Product ID, Name, Category, Brand, Unit, Quantity, Minimum Stock threshold, Supplier, and Rack Location.
- **Low Stock Alerts**: Products falling below their `minimum_stock` threshold are highlighted in red across the UI.
- **Search & Filtering**: Real-time search across product names, IDs, and rack locations, plus category filtering.

### 📝 Stock Operations & Ledger
- **Stock In (Receiving)**: Adds to inventory. Records Date, Quantity, Supplier (Optional), and Remarks.
- **Stock Out (Dispatch)**: Deducts from inventory. Validates against available stock (prevents negative stock). Records Date, Quantity, Customer/Site (Optional), Employee Name (Optional), and Remarks.
- **Ledger Table**: A unified chronological transaction history. 
  - The `Customer/Site` column displays the destination for dispatches.
  - The `Employee/Supplier` column displays the Supplier for inflows or the Employee for outflows.
- **Pagination & Search**: Handles large volumes of transactions with local pagination and dynamic search filters.

### 📄 Reports & Automations
- **Export Engine**: Generate transaction logs and current inventory status in **PDF** or **Excel** format. Supports filtering by Daily, Weekly, or Monthly ranges.
- **WhatsApp Integration**: Sends an automated daily summary of stock inflows/outflows and low-stock warnings to a configured WhatsApp number at 6:00 PM every day.
- **Settings Dashboard**: Allows administrators to configure their Meta API credentials (Phone ID, Token, Recipient Number) directly from the UI.

---

## 3. Directory Structure

```text
solar/
├── backend/
│   ├── app.py           # Main FastAPI server, API endpoints, and report generators
│   ├── scheduler.py     # Background job scheduler for daily reports
│   └── whatsapp.py      # Meta WhatsApp API integration logic
├── css/
│   └── style.css        # Comprehensive stylesheets, themes, and animations
├── data/
│   └── stock.json       # The JSON database (Products, Transactions, Configs)
├── js/
│   └── app.js           # Frontend SPA routing, state management, and API calls
├── reports/             # Temporary directory for generated PDF/Excel files
├── scratch/             # Testing and verification scripts (e.g., test_endpoints.py)
├── venv/                # Python virtual environment
└── index.html           # Main application shell and UI templates (Modals, Tables)
```

---

## 4. Backend API Endpoints (Functions)

The FastAPI backend (`backend/app.py`) exposes the following endpoints:

### Authentication
- `POST /api/login`: Validates credentials and issues a session token.
- `POST /api/logout`: Invalidates the current session token.

### Dashboard Data
- `GET /api/dashboard`: Aggregates metrics and chart data (inflows/outflows over 7 days, category counts).

### Product Catalog
- `GET /api/products`: Retrieves the full list of products.
- `POST /api/products`: Adds a new product to the catalog.
- `PUT /api/products/{product_id}`: Updates an existing product's details.
- `DELETE /api/products/{product_id}`: Removes a product from the catalog.

### Transactions & Ledger
- `GET /api/transactions`: Retrieves the full, chronologically sorted transaction ledger.
- `POST /api/stock-in`: Increments product quantity and logs a "STOCK IN" transaction.
- `POST /api/stock-out`: Decrements product quantity and logs a "STOCK OUT" transaction.

### Reports & Export
- `GET /api/reports/export`: Generates and streams a downloadable file (`.pdf` or `.xlsx`) containing the inventory status and transaction history for a given range (`daily`, `weekly`, `monthly`).

### Settings & WhatsApp
- `GET /api/whatsapp/config`: Retrieves currently saved Meta API configuration.
- `POST /api/whatsapp/config`: Saves updated Meta API configuration to the JSON file.
- `POST /api/whatsapp/test`: Instantly triggers a test WhatsApp notification report to verify connectivity.

---

## 5. Key Frontend Functions (`js/app.js`)

- `apiCall(endpoint, method, body)`: A central wrapper for `fetch` that automatically attaches the JWT token, handles errors, and parses JSON or Blob responses.
- `loadView(viewId)`: The SPA router. Hides all sections and displays the requested view, triggering the associated data fetch function (e.g., `loadDashboardData()`).
- `renderProductsTable()` / `renderTransactionsTable()`: Handles client-side pagination, search filtering, and DOM injection for tables.
- `renderProductStockSummary()`: Dynamically generates the visual progress bars for Solar Panels and Inverters based on maximum quantity limits.
- `downloadReportFile(format)`: Handles secure blob downloads for generated PDFs and Excel files requiring authorization headers.
