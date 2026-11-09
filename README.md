# FreelanceShield AI 🛡️
## AI-Powered Freelancer Protection & PayPal Automation Platform
*Built for the PayPal & AI Hackathon 2026*

[![Python](https://img.shields.io/badge/Python-3.14-087FA5.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-37BCD3.svg)](https://flask.palletsprojects.com)
[![PayPal](https://img.shields.io/badge/PayPal-Orders_v2_Sandbox-003087.svg)](https://developer.paypal.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-10A37F.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

FreelanceShield AI is a full-stack financial security and payment automation platform designed for independent software engineers, digital designers, and freelance contractors. It combines **AI-powered cybersecurity defense**, **real PayPal Sandbox Orders v2 payment processing**, and **AI-driven freelance business automation** inside an interface inspired by **Liquid Glass Fintech**.

---

## 🌊 Visual Design — Liquid Glass Fintech

FreelanceShield AI replaces boring admin dashboards with a liquid glass aesthetic:
- **Fluid Liquid Canvas**: Aqua blue (`#37BCD3`), turquoise (`#64D6DC`), and deep blue (`#087FA5`) liquid mesh with animated floating 3D ambient orbs.
- **Glassmorphism Surfaces**: Frosted white floating panels (`rgba(255, 255, 255, 0.75)` with `backdrop-filter: blur(20px)`), crisp 1px borders, and multi-layered elevation shadows.
- **High-Contrast Typography**: Plus Jakarta Sans and Inter typography for readability and accessibility.
- **Fintech Accents**: Orange (`#FF9D24`) for warnings and Coral (`#FF6565`) for critical security threats.

---

## ⚡ Three Integrated Systems

### 1. 🛡️ AI Cybersecurity Protection Center
- **Scam Message Detector**: Analyzes client messages and job offers for overpayment schemes, cashier's check tricks, fake escrow claims, and off-platform Telegram/WhatsApp coercion. Returns structured risk scores (0–100), risk classifications (Low, Medium, High, Critical), detected indicators, and safety recommendations.
- **Suspicious URL & Phishing Scanner**: Validates URL syntax, inspects domain properties, verifies HTTPS transport, detects raw IP hosts, flags punycode homoglyphs (`xn--`), and unmasks spoofed financial domains (e.g. `paypal.com-verify.top`) without navigating to malicious servers.
- **Freelance Job Offer Analyzer**: Evaluates freelance postings for upfront onboarding fee traps, unrealistic compensation (e.g. $90/hr data entry bait), sensitive government ID requests, and artificial urgency.

### 2. 💳 PayPal Payment Center (Orders v2 Sandbox)
- **Live Connection Monitor**: Displays active Sandbox connection status and token state.
- **Create Payment Orders**: Generates PayPal orders via Orders v2 API with Intent `CAPTURE`.
- **Approval & Capture**: Real PayPal Sandbox checkout flow with server-side capture verification.
- **Idempotent Transaction Ledger**: Tracks gross amounts, PayPal processing fees, net proceeds, client identities, and security risk ratings without duplicate records.
- **Forensic Inspector**: Slide-over drawer detailing transaction telemetry, geolocations, and escrow release status.

### 3. 🤖 AI Business Automation & Financial Assistant
- **AI Natural-Language Invoice Studio**: Type natural instructions such as *"Create an invoice for a $500 website development project for ABC Solutions due in 10 days"*. The AI extracts client names, project titles, amounts, and due dates into an editable review form.
- **Tamper-Evident PDF Invoices**: Generates production-grade, print-ready PDF invoices using ReportLab with itemized service tables, PayPal escrow seals, and payment references.
- **ShieldBot AI Financial Copilot**: Floating assistant accessible throughout the platform. Answers questions in natural language using **live SQLite database context** (e.g. *"How much money have I received?"*, *"Show pending payments"*, *"Which invoices are unpaid?"*).

---

## 🏗️ Architecture & Tech Stack

```
FreelanceShield AI Architecture
├── Frontend (Client Layer)
│   ├── HTML5 Liquid Glass Single-Page Architecture
│   ├── CSS3 Custom Properties & Glassmorphism Design System (style.css)
│   ├── Vanilla ES6+ Interactive Controller (app.js)
│   └── Chart.js 4.4 Data Visualizations (charts.js)
│
├── Backend (Flask Application Layer)
│   ├── REST API Endpoints (app.py)
│   ├── Session & CSRF Security Guards
│   └── Global Error Handlers (Zero Stack-Trace Leakage)
│
├── AI Security Engine
│   ├── OpenAI GPT-4o-mini Integration (ai_security_engine.py)
│   └── Precision NLP Heuristic Threat Signatures (Zero-key fallback)
│
├── PayPal Sandbox Service
│   ├── OAuth 2.0 Bearer Token Management (paypal_service.py)
│   ├── Orders v2 Create & Server-Side Capture
│   └── Webhook Signature Verification & Idempotency
│
├── Document Automation
│   └── ReportLab PDF Invoicing Pipeline (invoice_pdf.py)
│
└── Persistence Layer
    └── SQLite3 Thread-Safe Database (freelanceshield.db)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip package manager

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/freelanceshield-ai.git
cd freelanceshield-ai
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to configure your API keys (optional — the platform runs with full fidelity in Sandbox/Heuristic mode even without external keys):
```env
FLASK_SECRET_KEY=your_secret_key_here
PORT=5000

# Optional: OpenAI API Key (Built-in Heuristic Engine activates if omitted)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# PayPal Sandbox Developer Credentials
# Obtain from: https://developer.paypal.com/dashboard/applications/sandbox
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

### 3. Initialize Database & Run Server
```bash
python run.py
```
Or directly:
```bash
python app.py
```

Open your browser to:
**http://127.0.0.1:5000**

---

## 💳 PayPal Sandbox Setup Instructions

1. Visit the [PayPal Developer Dashboard](https://developer.paypal.com).
2. Log in and navigate to **Apps & Credentials** > **Sandbox**.
3. Create a new application named `FreelanceShield AI`.
4. Copy the **Client ID** and **Secret Key**.
5. Paste them into your `.env` file under `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`.
6. Start the server. The connection badge in the top navigation will display `Sandbox Live API Handshake`.
7. Use any standard PayPal Sandbox buyer test account to approve payment orders.

*Note: If no credentials are configured, FreelanceShield AI seamlessly activates high-fidelity Sandbox Simulation mode so judges can test all workflows without needing developer credentials.*

---

## 🧪 Automated Testing

Execute the comprehensive end-to-end test suite:
```bash
python test_app.py
```

**Test Coverage:**
- `test_01_index_page` — Verifies Liquid Glass SPA renders with HTTP 200.
- `test_02_dashboard_stats` — Verifies live database metrics calculation.
- `test_03_transactions_api` — Verifies ledger retrieval and filtering.
- `test_04_ai_scam_message_analysis` — Verifies scam detector on cashier check overpayments.
- `test_05_ai_url_scanner` — Verifies detection of spoofed brand domains and insecure HTTP.
- `test_06_ai_job_offer_analyzer` — Verifies detection of upfront fees and unrealistic rates.
- `test_07_ai_invoice_generator` — Verifies NLP parameter extraction from plain English.
- `test_08_invoice_crud_and_pdf` — Verifies ReportLab PDF generation and download.
- `test_09_paypal_sandbox_workflow` — Verifies Orders v2 creation and server capture.
- `test_10_ai_financial_assistant` — Verifies DB-grounded Q&A with live financial figures.
- `test_11_notifications_api` — Verifies security alarm feed and mark-read operations.

---

## 🎥 YouTube Demo Video Script (3–5 Minutes)

**Title:** *FreelanceShield AI — AI-Powered Cybersecurity & PayPal Automation for Freelancers*

| Time | Scene | Visual | Voiceover / Narration |
|---|---|---|---|
| **0:00 - 0:35** | **The Problem & Hero Intro** | Show Landing Page (`#landing`) with flowing Liquid Glass aqua background and 3D glowing telemetry. | *"Freelancers lose millions annually to fraudulent chargebacks, spoofed PayPal emails, fake cashier's checks, and malicious phishing links. Welcome to FreelanceShield AI — the financial security platform built for the PayPal and AI Hackathon."* |
| **0:35 - 1:15** | **Command Dashboard** | Click **Get Started** to transition to `#dashboard`. Show 6 live glass cards, animated Chart.js curves, and transaction ledger. | *"Our Liquid Glass dashboard unifies freelance finance. Every figure here is backed by real SQLite database records — showing $34,820 in verified PayPal payments, $4,200 pending in escrow, and zero chargeback losses."* |
| **1:15 - 2:00** | **AI Security Center in Action** | Switch to `#security`. Click the **Cashier's Check Scam** preset and hit **Analyze**. Show the circular risk meter hitting 80 Critical. | *"Let's test an incoming client proposal. A client offers to send an $8,500 check and asks us to wire $2,000 back on Telegram. One click, and our AI Security Engine flags an 80/100 Critical Risk, identifies the exact overpayment and off-platform evasion patterns, and generates an immediate alert."* |
| **2:00 - 2:30** | **Suspicious URL Scanner** | Switch to the **URL Scanner** tab. Click **PayPal Impersonator (.top)** preset and run scan. | *"Next, the client sends a link to 'verify' payment. Our URL scanner checks DNS and protocol heuristics without visiting dangerous servers. It immediately catches the fake `.top` domain and brand impersonation, keeping the freelancer safe."* |
| **2:30 - 3:15** | **PayPal Sandbox Payment Flow** | Switch to `#paypal`. Click **+ Create Payment Request**, enter $500 for Apex Cloud Systems, and submit. Open checkout modal and click **Approve & Capture**. | *"Now for payment: We create a PayPal Sandbox order for $500. Our backend calls the PayPal Orders v2 API. Once the buyer authorizes in sandbox, our server captures the order, verifies the capture ID, calculates fees, and records the transaction idempotently."* |
| **3:15 - 3:55** | **AI Invoicing & PDF Generation** | Switch to `#invoices`. Type: *'Create an invoice for a $500 website development project for ABC Solutions due in 10 days'*. Hit **Generate**. Click **PDF**. | *"Invoicing is effortless. We enter a single natural language sentence. ShieldBot extracts the client name, line items, and due date. We save it, and with one click, ReportLab builds a print-ready PDF invoice with an embedded PayPal escrow security seal."* |
| **3:55 - 4:30** | **ShieldBot Copilot & Conclusion** | Click floating **ShieldBot Copilot**. Click *'How much money have I received?'*. Show exact DB answer. | *"Finally, our floating AI copilot ShieldBot has real-time access to our SQLite ledger. When we ask how much we've received, it answers with exact figures from our verified payments — never hallucinating. FreelanceShield AI: Your freelance business. Protected."* |

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
