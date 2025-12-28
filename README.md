# 🧖‍♀️ Spa Management API

A **production-ready backend API** for managing a Spa / Wellness business, built with **FastAPI, SQLAlchemy, and PostgreSQL**.

Designed to demonstrate **real-world business logic**, role-based security, payments, dashboards, and third-party integrations (WhatsApp).

---

## 🔑 Key Highlights

- **FastAPI + SQLAlchemy 2.0**
- **JWT Authentication & Role-Based Access**
- **Appointment lifecycle management**
- **Payments & revenue tracking**
- **Admin dashboards**
- **WhatsApp Business API integration**
- **Audit logging (price & financial changes)**
- **Media management (images, sliders, gallery)**

---

---

## 🚀 Features

## 👥 Roles & Permissions

- **ADMIN** – Full access
- **RECEPTIONIST** – Appointments, payments, validation
- **EMPLOYEE** – Assigned appointments
- **CUSTOMER** – Booking & confirmations

## 📅 Appointments

- Customers request appointments
- Receptionists/Admins validate
- Customers confirm
- Cancelation allowed at any time (no refunds' policy)

Statuses:
- - REQUESTED → VALIDATED → CONFIRMED → DONE
↘ CANCELED / NO_SHOW

---

### 💰 Payments & Revenue
- Supports multiple payment methods:
- `CASH`
- `TRANSFER`
- `CARD`
- Partial payments supported (e.g. 50% deposit)
- **No refunds policy** (cancelled appointments still count as revenue)
- Revenue dashboards:
- Revenue by day / month
- Revenue by payment method
- Revenue by appointment status

---

### 🧾 Cash Entries
- Tracks all financial movements
- Linked optionally to appointments
- Fully auditable (who changed what and when)

---

### 🛠 Services & 🛒 Products
- CRUD endpoints
- Image upload support (with replace & cleanup)
- Price auditing (tracks historical price changes)
- Active / inactive states

---

### 🖼 Media Management
- **Slides / Sliders**
- Image upload
- Manual ordering (reorder endpoint)
- Enable / disable slides
- **Gallery**
- Simple image gallery for frontend
- **Testimonials**
- Name
- Description
- Image
- Date

---

### ⚙️ Site Settings (CMS-like)
Centralized configuration for the public website:
- Application name
- About text
- Contact phone (WhatsApp)
- Google Maps iframe
- Social links (Instagram, Facebook, X, etc.)
- Multiple logos:
- Main logo
- Sidebar logo
- Small logo

---

### 📲 WhatsApp Integration
- WhatsApp Business Cloud API (Meta)
- Template-based notifications:
- Appointment validated
- Appointment confirmed
- Opt-in compliance (`whatsapp_opt_in`)

---

### 🧑‍💼 Audit Logging
Audits changes for:
- Services
- Products
- Cash entries

Tracks:
- Action (`CREATE`, `UPDATE`, `DELETE`)
- Changed fields (JSON diff)
- Actor user (`actor_user_id`)
- Timestamp

---

## 🧱 Tech Stack

- **Python 3.11+**
- **FastAPI**
- **SQLAlchemy 2.0**
- **PostgreSQL**
- **Alembic**
- **Pydantic v2**
- **JWT (Auth)**
- **HTTPX**
- **WhatsApp Cloud API**
- **Docker-ready**

---

## 📁 Project Structure
```aiignore
app/
├── api/
│ └── v1/
│ ├── auth.py
│ ├── appointments.py
│ ├── services.py
│ ├── products.py
│ ├── cash.py
│ ├── dashboard.py
│ ├── users.py
│ └── public.py
├── core/
│ ├── config.py
│ ├── db.py
│ ├── security.py
│ └── audit.py
├── integrations/
│ └── whatsapp_meta.py
├── models/
├── schemas/
├── middleware/
└── main.py
```

---

## ⚙️ Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/spa_db
JWT_SECRET=supersecretkey
JWT_ALG=HS256

TIMEZONE=America/Santo_Domingo
CURRENCY=DOP

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=your_email

WA_PHONE_NUMBER_ID=xxxxxxxxxxxx
WA_ACCESS_TOKEN=EAAG...
WA_DEFAULT_LANG=es
```

## Create migration
alembic revision -m "your message"

## Apply migrations
alembic upgrade head

## Run the App
uvicorn app.main:app --reload

Swagger UI:
http://localhost:8000/docs

## 👨‍💻 Author
- Andrés Frias
- Senior Full Stack Developer
- Java · Spring Boot · Angular · FastAPI

