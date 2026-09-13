# SmartMed

**AI Medicine Reminder & Verification System**

SmartMed is a college major-project application that helps a person remember medicines they have already registered, and compare a scanned package with that saved record.

This is an **educational / engineering** system. It does **not** diagnose medical conditions, prescribe medicines, recommend dosages, modify prescriptions, or tell anyone that a medicine is medically safe to take.

A successful scan is reported as:

> Detected medicine appears to match your saved medicine.

If the labels differ, SmartMed reports that the medicine **does not appear to match**. When uncertain, check the package and prescription, or contact a pharmacist or healthcare professional.

---

## Problem statement

People miss scheduled doses, and it is easy to pick up the wrong blister pack when several medicines look similar. Students need a demonstrable, locally runnable system that:

- stores user-entered medicine records and schedules
- shows due and upcoming reminders
- captures a package photo from a camera or file
- reads printed text with OCR and a barcode when one is visible
- compares that result with the saved record
- records taken / missed / skipped doses for adherence statistics

## Features

- Registration and login with PBKDF2 password hashing and JWT sessions
- Dashboard: today’s medicines, upcoming slot, taken/missed counts, 7-day adherence, expiring medicines, recent history
- Add, edit, and delete medicines
- Schedule rows: daily, weekly, or every other day
- Camera capture, photo upload, and optional live barcode scanning (`html5-qrcode`)
- OpenCV preprocessing + Tesseract OCR + barcode detection
- Match / mismatch / low-confidence / no-text verification states
- Dose history and caregiver missed-dose alerts (email if SMTP is configured)
- Responsive healthcare-style UI with loading, empty, error, success, and confirm states

## Architecture

```
Browser (React / Vite)
        |  REST
FastAPI  —  Auth (PBKDF2 + JWT)
         —  Medicines / schedules / dose history / caregivers
         —  OCR module (OpenCV → Tesseract → name cleanup)
         —  Verification matcher (name similarity + barcode)
         —  SQLite via SQLAlchemy
```

The OCR package (`backend/app/ocr/`) is intentionally separate so a later team can replace Tesseract with a stronger vision model without rewriting reminders or the dashboard.

## Technology stack

| Layer | Tools |
| --- | --- |
| Frontend | React 18, Vite, JavaScript, responsive CSS, html5-qrcode |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite |
| Vision | OpenCV, Tesseract OCR, optional pyzbar if ZBar is installed |
| Auth | PBKDF2-HMAC-SHA256, JWT (`JWT_SECRET` from environment) |

## Project structure

```
smartmed/
  frontend/          React client
  backend/
    app/
      api/           HTTP routes
      models/        SQLAlchemy tables
      schemas/       Pydantic models
      services/      auth, matching, analytics, notifications
      ocr/           replaceable scan pipeline
      database/      engine and sessions
      main.py
    tests/
    .env.example
  README.md
```

## Database

| Table | Purpose |
| --- | --- |
| `users` | name, email, password hash |
| `medicines` | saved medicine record for one user |
| `schedules` | clock time, frequency, start/end dates |
| `dose_history` | taken / missed / skipped + verification result |
| `caregivers` | optional missed-dose contacts |

## Installation

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Put the printed value into `backend/.env` as `JWT_SECRET`. Leave `DEMO_PASSWORD` as a local development password only.

Create folders used by SQLite:

```bash
mkdir -p data uploads
```

### 2. OCR setup (Tesseract)

macOS:

```bash
brew install tesseract
```

Ubuntu / Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

If the binary is not on `PATH`, set `TESSERACT_CMD` in `.env` to the full path.

Optional 1D barcode support:

```bash
brew install zbar
pip install pyzbar
```

OpenCV QR detection still works without ZBar.

### 3. Frontend

```bash
cd frontend
npm install
```

## Running locally

Terminal 1 — API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — UI:

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite app calls the API at `http://127.0.0.1:8000` (see `frontend/.env.example`).

If port 5173 is already in use, Vite will choose 5174. Add that origin to `CORS_ORIGINS` in `backend/.env`.

Seeded demo login (only when the database is empty and `SMARTMED_SEED=true`):

- Email: `demo@smartmed.local`
- Password: value of `DEMO_PASSWORD` (default `DemoPass123`)

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Database setup

SQLite is created automatically on API startup at `backend/data/smartmed.db` (or `DATABASE_URL`). Tables are created with SQLAlchemy `create_all`. No separate migration step is required for this MVP.

To reset demo data, stop the API, delete `backend/data/smartmed.db`, and start again.

## API documentation

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Sign in |
| GET | `/auth/me` | Current user |
| GET/POST | `/medicines` | List / create medicines |
| GET/PUT/DELETE | `/medicines/{id}` | Read / update / delete |
| GET/POST | `/schedules` | List / create schedules |
| PUT/DELETE | `/schedules/{id}` | Update / delete a schedule |
| POST | `/verification/scan` | Photo and/or barcode comparison |
| GET/POST | `/dose-history` | List / record a dose |
| GET | `/analytics` | Dashboard statistics |
| GET | `/reminders` | Today’s reminder slots |
| GET/POST | `/caregivers` | Caregiver contacts |
| GET | `/health` | API and OCR availability |

`POST /verification/scan` is `multipart/form-data` with `medicine_id`, optional `file`, and optional `barcode`.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Tests cover registration, login, medicine CRUD, schedules, verification matching, dose history, analytics, caregivers, and seed data. Photo OCR is mocked so pytest does not require Tesseract.

## Screenshots

Add viva screenshots here after a local run:

- Login
- Dashboard
- Medicine list / form
- Camera verification (match)
- Camera verification (mismatch)
- Dose history

## Safety limitations

- OCR and barcodes can misread damaged, reflective, or handwritten labels.
- A match is **not** proof of identity, authenticity, or clinical correctness.
- Expiry warnings use the date **you typed**, not an independent check of the physical pack.
- Caregiver messages are schedule notifications, not clinical alerts.
- Do not use SmartMed as a substitute for a pharmacist, prescriber, or labelled instructions.

## Future improvements

- Swap Tesseract for a dedicated medicine-pack vision model
- Push notifications and a mobile wrapper
- Multi-language OCR
- Shared family accounts with explicit consent
- Proper email/SMS delivery receipts
- Encrypted backups and audited access logs

## License

Educational project use.
