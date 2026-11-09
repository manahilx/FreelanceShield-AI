"""
FreelanceShield AI - SQLite Database Engine & Data Access Layer
Handles schemas, constraints, indexing, notifications creation, and realistic demo seeds.
"""

import sqlite3
import os
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freelanceshield.db")

def get_db_connection():
    """Returns a thread-safe connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes all required database tables and seeds demo data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'freelancer',
        created_at TEXT NOT NULL
    )
    """)

    # 2. Invoices Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id TEXT PRIMARY KEY,
        invoice_number TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        client_email TEXT NOT NULL,
        project_title TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        status TEXT NOT NULL, -- 'Paid', 'Pending', 'Unpaid', 'Overdue'
        due_date TEXT NOT NULL,
        paypal_order_id TEXT,
        items_json TEXT, -- JSON array of line items
        pdf_path TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 3. Transactions Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        paypal_order_id TEXT,
        paypal_capture_id TEXT,
        client_name TEXT NOT NULL,
        client_email TEXT NOT NULL,
        client_company TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        payment_status TEXT NOT NULL, -- 'Completed', 'Pending', 'Failed', 'Cancelled'
        ai_risk_score INTEGER NOT NULL, -- 0 to 100
        security_status TEXT NOT NULL, -- 'Safe', 'Review', 'Suspicious'
        risk_reason TEXT,
        paypal_fee REAL DEFAULT 0.0,
        net_amount REAL DEFAULT 0.0,
        ip_address TEXT,
        country TEXT,
        is_sandbox BOOLEAN DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 4. Security Reports Entity (Message, URL & Job Scans)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_reports (
        id TEXT PRIMARY KEY,
        report_type TEXT NOT NULL, -- 'message', 'url', 'job'
        input_data TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_classification TEXT NOT NULL, -- 'Low', 'Medium', 'High', 'Critical'
        detected_indicators_json TEXT,
        risk_explanation TEXT NOT NULL,
        recommendations_json TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 5. Notifications Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL, -- 'Critical', 'High', 'Medium', 'Info'
        is_read INTEGER DEFAULT 0,
        related_entity_type TEXT, -- 'transaction', 'security_report', 'invoice'
        related_entity_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 6. Client Records Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS client_records (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        company TEXT,
        trust_score INTEGER DEFAULT 95, -- 0 to 100
        verification_status TEXT DEFAULT 'Verified',
        total_paid REAL DEFAULT 0.0,
        dispute_rate REAL DEFAULT 0.0,
        country TEXT DEFAULT 'United States',
        avatar_initials TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 7. AI Activity Logs Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_activity_logs (
        id TEXT PRIMARY KEY,
        query_type TEXT NOT NULL, -- 'message_scan', 'url_scan', 'job_scan', 'invoice_gen', 'assistant'
        user_prompt TEXT,
        response_summary TEXT,
        model_name TEXT,
        execution_time_ms INTEGER,
        created_at TEXT NOT NULL
    )
    """)

    # 8. Projects Entity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        client_name TEXT NOT NULL,
        client_email TEXT NOT NULL,
        budget REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        escrow_status TEXT NOT NULL, -- 'Secured', 'Pending Deposit', 'Released'
        security_level TEXT NOT NULL, -- 'Verified', 'Monitored', 'Elevated Risk'
        progress INTEGER DEFAULT 0,
        due_date TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

    seed_database_if_empty()

def add_notification(title, description, severity="Info", related_type=None, related_id=None):
    """Utility to inject an event notification into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    notif_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO notifications (id, title, description, severity, is_read, related_entity_type, related_entity_id, created_at)
    VALUES (?, ?, ?, ?, 0, ?, ?, ?)
    """, (notif_id, title, description, severity, related_type, related_id, now_str))
    conn.commit()
    conn.close()
    return notif_id

def log_ai_activity(query_type, user_prompt, response_summary, model_name="OpenAI / Built-in Heuristic", time_ms=120):
    """Records AI queries and outputs for telemetry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        log_id = f"AILOG-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO ai_activity_logs (id, query_type, user_prompt, response_summary, model_name, execution_time_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (log_id, query_type, (user_prompt or "")[:500], (response_summary or "")[:500], model_name, time_ms, now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Warning] Could not log AI activity: {e}")

def seed_database_if_empty():
    """Seeds initial realistic data for testing and hackathon demo evaluation."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.now()

    # 1. Default Demo User
    demo_user_id = "USR-DEV-001"
    hashed_pw = generate_password_hash("FreelanceShield2026!")
    cursor.execute("""
    INSERT INTO users (id, username, email, password_hash, full_name, role, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (demo_user_id, "demo_freelancer", "freelancer@shield.dev", hashed_pw, "Alex Rivers", "freelancer", now.strftime("%Y-%m-%d %H:%M:%S")))

    # 2. Clients
    demo_clients = [
        ("CLI-01", "Sarah Jenkins", "s.jenkins@apexcloud.io", "Apex Cloud Systems", 99, "Verified", 14250.00, 0.0, "United States", "SJ", (now - timedelta(days=90)).strftime("%Y-%m-%d")),
        ("CLI-02", "Amira Al-Mansoor", "amira@finshield.ae", "FinShield Fintech", 98, "Verified", 9300.00, 0.0, "UAE", "AA", (now - timedelta(days=60)).strftime("%Y-%m-%d")),
        ("CLI-03", "David Kovacs", "dkovacs@novatech.de", "NovaTech Solutions", 96, "Verified", 6850.00, 0.0, "Germany", "DK", (now - timedelta(days=45)).strftime("%Y-%m-%d")),
        ("CLI-04", "Marcus Sterling", "msterling.consult@gmail.com", "Sterling Media Group", 94, "Verified", 3290.00, 0.0, "United States", "MS", (now - timedelta(days=30)).strftime("%Y-%m-%d")),
        ("CLI-05", "Elena Rostova", "erostova@cyberexplore.uk", "CyberExplore Ltd", 72, "Under Review", 4200.00, 2.1, "United Kingdom", "ER", (now - timedelta(days=12)).strftime("%Y-%m-%d")),
        ("CLI-06", "Global Escrow Entity", "security-notice@paypal-verify-escrow.top", "Unknown Off-platform", 12, "Blocked", 0.00, 100.0, "Seychelles", "GE", (now - timedelta(days=3)).strftime("%Y-%m-%d")),
    ]
    cursor.executemany("""
    INSERT INTO client_records (id, name, email, company, trust_score, verification_status, total_paid, dispute_rate, country, avatar_initials, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_clients)

    # 3. Transactions (clearly tagged as Sandbox or verified milestone payments)
    demo_transactions = [
        ("TXN-98421", "PP-ORD-88210394", "PP-CAP-55112201", "Sarah Jenkins", "s.jenkins@apexcloud.io", "Apex Cloud Systems", 2850.00, "USD", "Completed", 3, "Safe", "Verified PayPal business account, verified IP origin, zero dispute record.", 85.50, 2764.50, "198.51.100.42", "United States", 1, (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98420", "PP-ORD-77192041", "PP-CAP-44332219", "David Kovacs", "dkovacs@novatech.de", "NovaTech Solutions", 1450.00, "USD", "Completed", 8, "Safe", "Standard recurring monthly milestone payment, valid SSL certificate, clean telemetry.", 43.50, 1406.50, "84.115.12.8", "Germany", 1, (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98419", "PP-ORD-66281099", None, "Elena Rostova", "erostova@cyberexplore.uk", "CyberExplore Ltd", 4200.00, "USD", "Pending", 42, "Review", "High first-time milestone release. PayPal Sandbox hold in effect awaiting buyer clearance.", 126.00, 4074.00, "51.140.89.21", "United Kingdom", 1, (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98418", "PP-ORD-55419082", "PP-CAP-33221190", "Marcus Sterling", "msterling.consult@gmail.com", "Sterling Media Group", 890.00, "USD", "Completed", 5, "Safe", "Clean transaction velocity, client verified, matching billing country.", 26.70, 863.30, "172.56.21.90", "United States", 1, (now - timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98417", "PP-ORD-44910237", None, "Global Escrow Entity", "security-notice@paypal-verify-escrow.top", "Unknown Entity", 3800.00, "USD", "Failed", 94, "Suspicious", "Overpayment scam pattern: spoofed domain (.top), mismatched proxy origin, fake escrow claim.", 0.00, 0.00, "185.220.101.5", "Seychelles", 1, (now - timedelta(days=2, hours=5)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=2, hours=5)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98416", "PP-ORD-33819205", "PP-CAP-22119933", "Amira Al-Mansoor", "amira@finshield.ae", "FinShield Fintech", 3100.00, "USD", "Completed", 6, "Safe", "Enterprise multi-signature client, authentic PayPal business checkout token.", 93.00, 3007.00, "185.12.98.4", "UAE", 1, (now - timedelta(days=3, hours=1)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=3, hours=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("TXN-98415", "PP-ORD-22910481", "PP-CAP-11998844", "Lucas Morel", "lmorel@studiohyper.fr", "Studio Hyper", 650.00, "USD", "Completed", 11, "Safe", "Fast checkout capture, valid developer sandbox payment.", 19.50, 630.50, "194.206.12.18", "France", 1, (now - timedelta(days=4, hours=6)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=4, hours=6)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany("""
    INSERT INTO transactions (id, paypal_order_id, paypal_capture_id, client_name, client_email, client_company, amount, currency, payment_status, ai_risk_score, security_status, risk_reason, paypal_fee, net_amount, ip_address, country, is_sandbox, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_transactions)

    # 4. Invoices
    demo_invoices = [
        ("INV-1001", "FS-INV-2026-001", "Sarah Jenkins", "s.jenkins@apexcloud.io", "Enterprise Cloud Security Audit", "Full architecture vulnerability evaluation and penetration assessment report.", 2850.00, "USD", "Paid", (now - timedelta(days=1)).strftime("%Y-%m-%d"), "PP-ORD-88210394", json.dumps([{"desc": "Architecture Security Audit", "qty": 1, "rate": 2000.00, "amount": 2000.00}, {"desc": "Penetration Testing Dossier", "qty": 1, "rate": 850.00, "amount": 850.00}]), None, (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("INV-1002", "FS-INV-2026-002", "David Kovacs", "dkovacs@novatech.de", "OAuth2 & JWT Microservice Auth", "Implementation of secure identity token authentication flow with refresh rotation.", 1450.00, "USD", "Paid", (now - timedelta(days=2)).strftime("%Y-%m-%d"), "PP-ORD-77192041", json.dumps([{"desc": "OAuth2 Implementation", "qty": 1, "rate": 1450.00, "amount": 1450.00}]), None, (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("INV-1003", "FS-INV-2026-003", "Elena Rostova", "erostova@cyberexplore.uk", "AI Vulnerability Scanning Pipeline", "Building automated heuristics for code repository security scanning.", 4200.00, "USD", "Pending", (now + timedelta(days=5)).strftime("%Y-%m-%d"), "PP-ORD-66281099", json.dumps([{"desc": "Heuristic Pipeline Core", "qty": 1, "rate": 3000.00, "amount": 3000.00}, {"desc": "CI/CD Integration", "qty": 1, "rate": 1200.00, "amount": 1200.00}]), None, (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        ("INV-1004", "FS-INV-2026-004", "Marcus Sterling", "msterling.consult@gmail.com", "Fintech Liquid Glass UI Design", "Complete Figma design system and responsive dashboard prototypes.", 1200.00, "USD", "Unpaid", (now + timedelta(days=10)).strftime("%Y-%m-%d"), None, json.dumps([{"desc": "Liquid Glass UI Design System", "qty": 1, "rate": 1200.00, "amount": 1200.00}]), None, (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("INV-1005", "FS-INV-2026-005", "Amira Al-Mansoor", "amira@finshield.ae", "PayPal Smart Checkout Integration", "End-to-end PayPal Orders v2 integration with webhooks and signature verification.", 3100.00, "USD", "Paid", (now - timedelta(days=3)).strftime("%Y-%m-%d"), "PP-ORD-33819205", json.dumps([{"desc": "Orders API Integration", "qty": 1, "rate": 2000.00, "amount": 2000.00}, {"desc": "Webhook Hardening", "qty": 1, "rate": 1100.00, "amount": 1100.00}]), None, (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany("""
    INSERT INTO invoices (id, invoice_number, client_name, client_email, project_title, description, amount, currency, status, due_date, paypal_order_id, items_json, pdf_path, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_invoices)

    # 5. Security Reports (Demonstration historical scans)
    demo_reports = [
        ("REP-801", "message", "Hello! I saw your profile and want to hire you for a $6,000 project. I will send you a cashier's check for $8,500. Please deposit it and wire the extra $2,500 to my supplier on Telegram @vendor_fastpay.", 96, "Critical", json.dumps(["Overpayment Cashier's Check Scam", "Third-party wire request", "Off-platform Telegram bypass"]), "Severe overpayment scam detected. Fake check will bounce after freelancer wires real money to scammer.", json.dumps(["Never accept checks with requests to refund excess funds.", "Block user and report account.", "Insist on verified PayPal Sandbox/Escrow."]), json.dumps({"source": "Upwork Message", "chars": 234}), (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("REP-802", "url", "https://paypal.com-verify-security-milestone.top/login?token=8921", 92, "Critical", json.dumps(["Suspicious TLD .top", "Deceptive brand impersonation (paypal.com-*)", "Phishing login path"]), "High-severity credential harvesting site masquerading as official PayPal verification page.", json.dumps(["Do NOT enter credentials or passwords.", "Block domain at network DNS.", "Report URL to PayPal Security Abuse."]), json.dumps({"domain": "paypal.com-verify-security-milestone.top", "tld": ".top", "protocol": "https"}), (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("REP-803", "job", "Looking for data entry specialist. $95/hour. Must pay $150 refundable equipment onboarding license fee before starting. Contact me on WhatsApp +1-202-555-0199.", 88, "High", json.dumps(["Unrealistic compensation for low-skill role", "Upfront onboarding fee demand", "Off-platform WhatsApp recruitment"]), "Typical advance fee fake job listing targeting remote freelancers.", json.dumps(["Never pay an employer or client to start working.", "Refuse off-platform communication."]), json.dumps({"hourly_rate": 95, "upfront_fee": 150}), (now - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany("""
    INSERT INTO security_reports (id, report_type, input_data, risk_score, risk_classification, detected_indicators_json, risk_explanation, recommendations_json, metadata_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_reports)

    # 6. Notifications
    demo_notifications = [
        ("NOTIF-101", "Critical Scam Message Blocked", "High-risk overpayment cashier's check scheme detected from unverified client proposal.", "Critical", 0, "security_report", "REP-801", (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("NOTIF-102", "Phishing Link Neutralized", "Spoofed PayPal domain 'paypal.com-verify-*.top' flagged and quarantined.", "High", 0, "security_report", "REP-802", (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")),
        ("NOTIF-103", "PayPal Sandbox Payment Captured", "Successfully captured $2,850.00 from Sarah Jenkins (Order ID: PP-ORD-88210394).", "Info", 1, "transaction", "TXN-98421", (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")),
        ("NOTIF-104", "New AI Invoice Generated", "Invoice FS-INV-2026-004 created for Marcus Sterling ($1,200.00 USD).", "Info", 1, "invoice", "INV-1004", (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("NOTIF-105", "Sandbox Escrow Under Clearance", "Payment of $4,200.00 from Elena Rostova is pending standard sandbox milestone verification.", "Medium", 0, "transaction", "TXN-98419", (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany("""
    INSERT INTO notifications (id, title, description, severity, is_read, related_entity_type, related_entity_id, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_notifications)

    # 7. Projects
    demo_projects = [
        ("PRJ-101", "Enterprise Cloud Security Audit", "Sarah Jenkins", "s.jenkins@apexcloud.io", 5700.00, "USD", "Secured", "Verified", 85, (now + timedelta(days=8)).strftime("%Y-%m-%d"), (now - timedelta(days=14)).strftime("%Y-%m-%d")),
        ("PRJ-102", "Fintech Payment Gateway Integration", "Amira Al-Mansoor", "amira@finshield.ae", 6200.00, "USD", "Secured", "Verified", 60, (now + timedelta(days=15)).strftime("%Y-%m-%d"), (now - timedelta(days=10)).strftime("%Y-%m-%d")),
        ("PRJ-103", "Decentralized Auth Architecture", "David Kovacs", "dkovacs@novatech.de", 3400.00, "USD", "Secured", "Verified", 40, (now + timedelta(days=21)).strftime("%Y-%m-%d"), (now - timedelta(days=5)).strftime("%Y-%m-%d")),
        ("PRJ-104", "AI Vulnerability Scanning Pipeline", "Elena Rostova", "erostova@cyberexplore.uk", 4200.00, "USD", "Pending Deposit", "Elevated Risk", 20, (now + timedelta(days=30)).strftime("%Y-%m-%d"), (now - timedelta(days=2)).strftime("%Y-%m-%d")),
        ("PRJ-105", "Fintech Liquid Glass UI Redesign", "Marcus Sterling", "msterling.consult@gmail.com", 2400.00, "USD", "Secured", "Verified", 95, (now + timedelta(days=3)).strftime("%Y-%m-%d"), (now - timedelta(days=12)).strftime("%Y-%m-%d")),
    ]
    cursor.executemany("""
    INSERT INTO projects (id, title, client_name, client_email, budget, currency, escrow_status, security_level, progress, due_date, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_projects)

    conn.commit()
    conn.close()
    print("[Database] FreelanceShield AI SQLite Database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
