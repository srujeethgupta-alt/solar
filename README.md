<div align="center">

# ☀️ New High Energy Solar — Stock Management System

**A full‑featured inventory, energy forecasting, and reporting platform for solar equipment dealers.**

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Energy Forecasting](#-energy-forecasting)
- [Notification Channels](#-notification-channels)
- [Reports & Export](#-reports--export)
- [Security](#-security)
- [Screenshots](#-screenshots)
- [Development](#-development)
- [Production Deployment](#-production-deployment)
- [License](#-license)

---

## 🚀 Overview

New High Energy Solar is a **production‑ready inventory management system** purpose‑built for solar equipment wholesalers and retailers. It combines traditional stock control with **solar energy output forecasting**, **automated reporting**, and **dual notification channels** (Email + WhatsApp).

The entire system runs on a lightweight **Python + FastAPI** backend with a **vanilla JavaScript SPA** frontend — no node_modules, no build step, no database server required. All data is persisted to a single JSON file with atomic writes and automatic backups.

---

## ✨ Features

### 📦 Inventory Management
| Feature | Details |
|---|---|
| **Product CRUD** | Add, edit, delete products with ID, name, category, brand, unit, supplier, rack location |
| **Stock In / Stock Out** | Atomic transactions with automatic ID generation (T001, T002…) |
| **Low‑Stock Alerts** | Visual badges for items below minimum stock and out‑of‑stock items |
| **Supplier & Customer Directory** | Manage contacts with phone/email validation |
| **Image Upload** | Attach product images (JPEG/PNG/WebP/GIF, max 5 MB) |
| **Stock Status Overview** | Dashboard cards for total products, available stock, low‑stock and out‑of‑stock counts |

### 🔋 Solar Energy Forecasting
- **Per‑panel‑type calculator** — dynamically reads every solar panel product in the catalog
- **Pill‑button selector** with count multiplier (1–100 panels)
- **2×2 metric grid** showing:
  - kWh generated per day
  - Current output per day (**Ah** = kWh × 1000 ÷ 230 V)
  - CO₂ offset (kg/day)
  - Panel efficiency percentage
- **Live temperature** from frontend weather simulation (not manual input)
- **Peak Sun Hours** (PSH) configurable in Settings (1–14 hours)
- Temperature derating: —0.4 % per °C above 25 °C
- Only in‑stock panels (quantity > 0) are shown in the selector

### 📧 Email Notifications
- SMTP‑based daily and weekly report delivery
- HTML formatted tables with stock status, transactions, and low‑stock warnings
- **3 retries** with exponential backoff (2 s → 4 s → 8 s)
- SMTP connection test before sending
- Independent failure — email issues never block WhatsApp and vice‑versa

### 💬 WhatsApp Notifications (Meta Cloud API v21.0)
- Send daily / weekly stock summary reports via WhatsApp
- Uses official **Meta Cloud API** (no third‑party libraries)
- Configurable recipient phone number
- **3 retries** with exponential backoff
- Test‑send button in Settings UI

### 📊 Reports & Export
| Format | Periods | Contents |
|---|---|---|
| **PDF** | Daily, Weekly, Monthly | Summary indicators, transaction table, low‑stock warnings |
| **XLSX** (Excel) | Daily, Weekly, Monthly | 3 sheets: Summary, Product Catalog, Transaction History |
| Conditional formatting | — | Green fill for stock‑in rows, red fill for stock‑out, amber/red for low/out‑of‑stock quantities |

### 🎨 User Interface
- **Dark / Light theme** toggle with persisted preference
- **Glassmorphism design** with solar‑yellow accent (#FFC107) and electric blue (#0EA5E9)
- **Animated logo** — sun icon rotates continuously; staggered entrance + glow pulse on login page
- **Skeleton loaders**, offline detection banner, mobile‑responsive layout
- **Accessibility**: `prefers-reduced-motion` disables all animations
- Login page with full‑bleed solar farm background image and dark overlay

### ⚙️ Scheduler
- APScheduler singleton for daily (09:00) and weekly (Mon 09:00) reports
- `coalesce=True`, `misfire_grace_time=3600`
- Independent try/except blocks — Email failure never blocks WhatsApp and vice‑versa
- Heartbeat log every hour

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Data** | Single JSON file + atomic read/write + automatic backups |
| **Frontend** | Vanilla JavaScript (no framework), HTML5, CSS3 |
| **Charts** | Chart.js 4.4.1 (CDN) |
| **Icons** | Lucide (CDN) |
| **Fonts** | Inter, Outfit, JetBrains Mono (Google Fonts) |
| **PDF** | ReportLab |
| **XLSX** | OpenPyXL |
| **Scheduler** | APScheduler 3.10+ |
| **HTTP Client** | httpx (for WhatsApp API) |
| **Auth** | Bearer token (SHA‑256 hashed, server‑side session map) |

---

## 📁 Project Structure

```
solar/
├── backend/
│   ├── app.py              # FastAPI router — all endpoints, auth, middleware
│   ├── emailer.py           # SMTP email formatting & sending
│   ├── exceptions.py        # Global exception handler middleware
│   ├── json_storage.py      # Atomic JSON read/write with auto‑backups
│   ├── logger.py            # Rotating file + console logger
│   ├── requirements.txt     # Python dependencies
│   ├── run.py               # Production entry point
│   ├── scheduler.py         # APScheduler singleton (daily/weekly reports)
│   ├── security.py          # Password hashing, XSS sanitization, validation
│   └── whatsapp.py           # WhatsApp Cloud API v21.0 client
├── css/
│   └── style.css            # Complete stylesheet (~2000 lines)
├── data/
│   ├── stock.json           # Persistent store (products, transactions, config)
│   └── backups/             # Auto‑generated backups (max 50)
├── js/
│   ├── app.js               # SPA logic (~1425 lines)
│   └── solar3d.js           # 3D viewer (deprecated, removed from UI)
├── logs/                    # Rotating application logs
├── reports/                 # Generated PDF/XLSX exports
├── scratch/
│   └── test_endpoints.py    # API test script
├── .env                     # Environment variables (git‑ignored)
├── .env.example             # Environment template
├── .gitignore
├── implementation_plan.md
├── index.html               # Single‑page application entry point
└── production_audit_report.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Clone & enter
```bash
git clone https://github.com/srujeethgupta-alt/solar.git
cd solar
```

### 2. Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure
```bash
cp .env.example .env
# Edit .env with your SMTP credentials, secret key, etc.
```

### 5. Run
```bash
python -m backend.app
```

Server starts at **`http://127.0.0.1:8000`**  
Default login: **`admin` / `admin`**

> **Note:** The first run auto‑creates `data/stock.json` with sample products, suppliers, customers, and a default admin account if none exists.

---

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `8000` | Server port |
| `RELOAD` | `false` | Hot‑reload on code changes (dev only) |
| `SECRET_KEY` | *(required)* | 64‑char random string for token signing |
| `ADMIN_USERNAME` | `admin` | Admin login name |
| `ADMIN_PASSWORD` | `admin` | Admin password (change immediately!) |
| `ADMIN_SALT` | *(required)* | Random salt for password hashing |
| `EMAIL_SMTP_SERVER` | `smtp.gmail.com` | SMTP host |
| `EMAIL_SMTP_PORT` | `587` | SMTP port |
| `EMAIL_SENDER` | — | SMTP sender address |
| `EMAIL_PASSWORD` | — | SMTP password or app‑specific password |
| `EMAIL_RECIPIENT` | — | Default report recipient |

> **Important:** The admin password is **hashed** with SHA‑256 + salt and stored in `stock.json`. After first login, you can safely remove the plain‑text `ADMIN_PASSWORD` from `.env`.

### Settings UI (in‑app)
| Setting | Description |
|---|---|
| **Peak Sun Hours** | Solar irradiance hours per day (1–14) |
| **Email Config** | SMTP server, port, credentials, recipient |
| **WhatsApp Config** | Meta Cloud API phone number ID, token, recipient |
| **Theme** | Dark / Light mode, persisted in `localStorage` |

---

## 📡 API Reference

### Authentication
```
POST /api/login          { "username": "admin", "password": "admin" }
                       → { "success": true, "token": "..." }
POST /api/logout         Header: Authorization: Bearer <token>
```

All endpoints below require `Authorization: Bearer <token>` header.

### Products
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products` | List all products |
| `POST` | `/api/products` | Add product |
| `PUT` | `/api/products/{id}` | Update product |
| `DELETE` | `/api/products/{id}` | Delete product |
| `POST` | `/api/products/{id}/image` | Upload product image |

### Stock Operations
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/stock-in` | Add stock (atomic) |
| `POST` | `/api/stock-out` | Deduct stock (atomic, rejects oversell) |
| `GET` | `/api/transactions` | List all transactions (newest first) |

### Suppliers & Customers
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/suppliers` | List suppliers |
| `POST` | `/api/suppliers` | Add supplier |
| `PUT` | `/api/suppliers/{id}` | Update supplier |
| `DELETE` | `/api/suppliers/{id}` | Delete supplier |
| *(same pattern)* | `/api/customers/…` | Customer CRUD |

### Dashboard & Energy
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Metrics, charts, per‑panel energy forecast |
| | | `?temp_c=32` overrides default temperature |

### Notifications
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/email/config` | Get email config (password masked) |
| `POST` | `/api/email/config` | Save email config |
| `POST` | `/api/email/test-send` | Send daily test report |
| `POST` | `/api/email/test-send-weekly` | Send weekly test report |
| `GET` | `/api/whatsapp/config` | Get WhatsApp config |
| `POST` | `/api/whatsapp/config` | Save WhatsApp config |
| `POST` | `/api/whatsapp/test-send` | Send WhatsApp test message |

### Reports
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/reports/export` | `?range_type=daily|weekly|monthly&file_format=pdf|xlsx` |
| `GET` | `/api/reports/list` | List previously generated reports |

### Energy Settings
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/energy/config` | Get peak sun hours |
| `POST` | `/api/energy/config` | Save peak sun hours |

### Health
```
GET /api/health → { "status": "healthy", "version": "2.0.0", … }
```

---

## 🔋 Energy Forecasting

The energy forecast computes expected solar output for each panel type **individually**:

```
daily_kWh   = (watt_rating / 1000) × peak_sun_hours × temperature_derating
current_Ah  = daily_kWh × 1000 / 230          (grid‑tied AC voltage)
CO₂_kg      = daily_kWh × 0.85                 (Indian grid average)
efficiency  = min(watt_rating / 17.0, 24.0)    (normalised to 1000 W/m²)
```

- **Temperature derating:** —0.4 % per °C above 25 °C (STC reference)
- **Panel Rating** (W) is extracted from `model_capacity` field or product name regex
- The frontend passes `temp_c` from a weather simulation (random daily variation)
- Only panels with **category = "Solar Panels"** and **quantity > 0** appear

---

## 📬 Notification Channels

### Email
- SMTP‑based (Gmail, Outlook, or any SMTP server)
- Sends daily (09:00) and weekly (Monday 09:00) reports automatically
- Reports include: summary indicators, full transaction list, low‑stock warnings
- HTML + plain‑text dual format
- **3 retries** with 2 s → 4 s → 8 s backoff

### WhatsApp (Meta Cloud API v21.0)
- Official API at `https://graph.facebook.com/v21.0/{phone_number_id}/messages`
- Requires: **Phone Number ID**, **System User Token**, **Recipient Number**
- Auto‑sends daily / weekly summaries via scheduler
- **3 retries** with exponential backoff
- Independent from email — a WhatsApp failure never prevents email delivery

---

## 📄 Reports & Export

Access via **Reports** tab in the UI or directly via API.

### PDF (ReportLab)
- Title page with period metadata
- Low‑stock / out‑of‑stock warning table (red header)
- Full transaction history with green IN / red OUT rows
- Professional table layout with alternating row colours

### XLSX (OpenPyXL)
- **Summary sheet** — key indicators (total products, inflow/outflow totals)
- **Catalog sheet** — all products with conditional formatting on stock levels
  - 🔴 Red fill = out of stock
  - 🟡 Amber fill = below minimum stock
- **Transactions sheet** — all transactions with green IN / red OUT fills

---

## 🔐 Security

| Measure | Implementation |
|---|---|
| **Password Storage** | SHA‑256 hash with unique salt per installation |
| **Authentication** | Bearer token (64‑char hex), 7‑day expiry |
| **XSS Protection** | HTML entity encoding on all user input (`sanitize_html()`) |
| **Content Security Policy** | Strict CSP restricting scripts, styles, fonts, and images |
| **Security Headers** | `X‑Content‑Type‑Options: nosniff`, `X‑Frame‑Options: DENY`, `X‑XSS‑Protection`, `Referrer‑Policy` |
| **Input Validation** | Pydantic models with length limits, regex patterns, type coercion |
| **Image Upload** | MIME type whitelist, 5 MB size limit |
| **CORS** | Configurable origins (default open for development) |
| **Request Logging** | All requests logged with method, path, status, duration |
| **Atomic Writes** | JSON mutations use `update_json()` with RLock — no partial writes or race conditions |
| **Auto‑Backups** | Every stock mutation creates a timestamped backup (max 50) in `data/backups/` |

---

## 🖼 Screenshots

> *(Add your own screenshots here)*

| Login Page | Dashboard | Energy Forecast |
|---|---|---|
| Solar farm background, animated logo | Stock cards, charts, panel selector | 2×2 metric grid, pill buttons |

---

## 🧑‍💻 Development

### Run with hot reload
```bash
$env:RELOAD="true"; python -m backend.app
```

### Test all endpoints
```bash
python scratch/test_endpoints.py
```

### Data persistence
All data lives in `data/stock.json`. Backups are automatically created in `data/backups/` before every write (max 50, oldest removed).

### Clean up
```bash
# Remove logs
rm -rf logs/*
# Remove backups (keep latest)
ls -t data/backups/ | tail -n +6 | xargs -I {} rm "data/backups/{}"
```

---

## 🚢 Production Deployment

### Checklist
1. **Change default credentials** — update `ADMIN_PASSWORD` and `ADMIN_SALT` in `.env`
2. **Set `SECRET_KEY`** — generate a 64‑char random hex string
3. **Restrict CORS** — set `CORS_ORIGINS` to your domain
4. **Use a reverse proxy** — nginx or Caddy for HTTPS termination
5. **Run as a service** — use systemd (Linux) or NSSM (Windows) for auto‑restart
6. **Disable hot reload** — ensure `RELOAD=false`
7. **Monitor logs** — rotating logs in `logs/` directory

### Production start
```bash
python backend/run.py
# or directly:
python -m backend.app
```

> **Note:** The production entry point (`run.py`) sets `RELOAD=false` and starts Uvicorn with production‑friendly defaults.

---

## 📝 License

MIT

---

<div align="center">
  Built with ☀️ for solar energy businesses.
  <br>
  <a href="https://github.com/srujeethgupta-alt/solar">GitHub Repository</a>
</div>
