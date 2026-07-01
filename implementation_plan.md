# Implementation Plan - Solar Stock Management Web Application

Create a modern, responsive Stock Management Web Application with a solar-themed user interface, local JSON storage, a Python backend (FastAPI) for API requests and background processes, and scheduled automatic WhatsApp reports via Meta's Business Cloud API.

## User Review Required

> [!IMPORTANT]
> **Admin Account Credentials**: We will configure a default admin username (`admin`) and password (`solar123`). The user can change this password later or we can provide it in configuration.
> **Meta WhatsApp API Setup**: Since Meta WhatsApp Business Cloud API requires a Developer Account, a verified Phone Number ID, and a Permanent Access Token, we will provide a **Settings tab** in the web interface to allow the admin to input and save these credentials. We will store these in the config block of `stock.json`.

---

## Open Questions

> [!WARNING]
> 1. **WhatsApp API Send Mode**: By default, Meta Cloud API requires a pre-approved template for outgoing messages if there is no active 24-hour user interaction window. Free-form text messages are only allowed as responses.
>    * Would you like the backend to send the message as **free-form text** (requires you to send a message to the bot first once every 24 hours to open the window), or should we use the default template format? We recommend implementing the free-form text sender first, as it allows arbitrary text layout as requested, and providing a template option.
> 2. **Predefined Number**: Do you have a specific WhatsApp recipient number you want hardcoded in the server, or should it be configurable through the Settings UI? (We will make it configurable in the Settings UI by default so you can change it without code modifications).

---

## Proposed Changes & File Structure

```
project/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── app.js
├── data/
│   └── stock.json
├── reports/
└── backend/
    ├── app.py
    ├── scheduler.py
    ├── whatsapp.py
    └── requirements.txt
```

### [Data Layer]

#### [NEW] [stock.json](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/data/stock.json)
Initialize a JSON structure to manage products, transactions, and system configuration:
```json
{
  "products": [],
  "transactions": [],
  "config": {
    "admin_username": "admin",
    "admin_password_hash": "$2b$12$...",
    "whatsapp_recipient": "",
    "whatsapp_phone_number_id": "",
    "whatsapp_token": ""
  }
}
```

### [Backend Server]

#### [NEW] [requirements.txt](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/backend/requirements.txt)
Define backend packages:
* `fastapi` & `uvicorn` (Core web framework)
* `pydantic` (Data parsing/validation)
* `apscheduler` (Background scheduler)
* `httpx` (Async HTTP requests for Meta WhatsApp API)
* `openpyxl` (Excel report generation)
* `fpdf2` (PDF report generation)
* `passlib[bcrypt]` (Password hashing for secure admin login verification)
* `python-multipart` (Form parsing support)

#### [NEW] [whatsapp.py](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/backend/whatsapp.py)
Provide helper logic to interact with the Meta WhatsApp Business Cloud API:
* Read API credentials (`whatsapp_token`, `whatsapp_phone_number_id`, `whatsapp_recipient`) from configuration.
* Format the custom report text dynamically.
* Send an HTTP POST to `https://graph.facebook.com/v18.0/{phone_number_id}/messages`.
* Support text messages (for active customer service window) or template message fallbacks.

#### [NEW] [scheduler.py](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/backend/scheduler.py)
Handle the background scheduling:
* Start an APScheduler instance during FastAPI app startup.
* Define a cron job configured to run daily at `18:00` (6:00 PM) server time.
* The job loads stock data from `stock.json`, processes transactions from the current calendar day, compiles the standard notification text, and triggers `whatsapp.py` to transmit the report.

#### [NEW] [app.py](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/backend/app.py)
The primary entry point:
* Serve the static frontend:
  * Mount `/css` and `/js` directories.
  * Serve `index.html` at the root path (`/`).
* API endpoints:
  * `POST /api/login`: Authenticate admin user, return JWT or a session indicator.
  * `GET /api/products`: Retrieve all products from `stock.json`.
  * `POST /api/products`: Create a product.
  * `PUT /api/products/{id}`: Modify a product.
  * `DELETE /api/products/{id}`: Remove a product.
  * `POST /api/stock-in`: Record a stock-in event, auto-incrementing quantity.
  * `POST /api/stock-out`: Record a stock-out event, checking for sufficient stock and auto-decrementing quantity.
  * `GET /api/dashboard`: Aggregated dashboard metrics & chart datasets.
  * `GET /api/reports/export`: Endpoint triggers Excel/PDF file generation dynamically on the server and returns a streamable file download.
  * `GET /api/whatsapp/config`: View configuration details.
  * `POST /api/whatsapp/config`: Set WhatsApp API configuration parameters (token, phone number ID, recipient).
  * `POST /api/whatsapp/test-send`: Manually trigger a test report immediately to the configured WhatsApp phone number.

### [Frontend Application]

#### [NEW] [index.html](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/index.html)
Main HTML page using structural layout:
* Embed Inter/Outfit google fonts and Lucide icons (or fontawesome).
* Embed Chart.js via CDN.
* Login overlay section.
* Main application shell:
  * Vertical navigation sidebar.
  * Header showing current user, configuration panel link, and date/time.
  * Section view container (SPA structure: Dashboard, Products, Stock Operations, Reports, Settings).

#### [NEW] [style.css](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/css/style.css)
* Design styling: custom scrollbars, glassmorphic layout cards, animated dashboard stats.
* Alert styles: highlights rows containing low stock items in red, prefixes a warning indicator, and includes micro-animations.
* Mobile responsive configurations.

#### [NEW] [app.js](file:///c:/Users/asus/OneDrive%20-%20Vignan%20University/Desktop/solar/js/app.js)
Handles client routing, API synchronization, chart rendering, and modals:
* View Routing: Toggles section displays without reloading.
* Authentication management: Save session tokens in `localStorage`.
* Dashboard visual updating: Requests dashboard statistics, updates counters, builds and updates Chart.js figures.
* Product CRUD: Handles dynamic tables, searching, pagination, sorting, and dialog boxes.
* Transactions forms: Implements form submission validation, stock validation, and records transaction detail.
* Toast messages: An animated toast notification element for clean operations success/error feedback.

---

## Verification Plan

### Automated Verification
* Launch the backend application locally: `python backend/app.py` or `uvicorn backend.app:app --reload`.
* Perform API endpoint tests (using Python scripts or simple HTTP clients) to verify all CRUD actions on the mock JSON file.
* Test PDF/Excel report export files to make sure they open and contain correct formatting.

### Manual Verification
* Access the web interface in the browser.
* Test login verification.
* Navigate between tabs, execute search and sorting filters on the product catalog.
* Perform stock adjustments (In & Out), checking for low-stock highlights and alert toasts.
* Input dummy WhatsApp credentials and use the "Send Test Report" button to check the formatted report message payloads in logs, verifying structure matches the requested text.
