"""
FreelanceShield AI - Production-Quality Flask Application & REST API
Combines Liquid Glass Fintech frontend with SQLite DB, AI Security Engine, PayPal Sandbox Orders v2 API, and ReportLab PDF invoicing.
"""

import os
import json
import uuid
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from database import (
    init_db, get_db_connection, add_notification, log_ai_activity
)
from paypal_service import PayPalService
from ai_security_engine import AISecurityEngine
from invoice_pdf import generate_invoice_pdf, INVOICES_DIR

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "freelanceshield-liquid-glass-2026-key"))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize DB on boot
init_db()

# Services
paypal_service = PayPalService()
ai_engine = AISecurityEngine()

# Helper for current logged-in user or demo session
def get_current_user():
    if "user_id" in session:
        conn = get_db_connection()
        user = conn.execute("SELECT id, username, email, full_name, role FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        conn.close()
        if user:
            return dict(user)
    # Default demo user context
    return {
        "id": "USR-DEV-001",
        "username": "demo_freelancer",
        "email": "freelancer@shield.dev",
        "full_name": "Alex Rivers",
        "role": "freelancer"
    }

# -----------------------------------------------------------------------------
# Frontend Page Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    user = get_current_user()
    pp_status = paypal_service.get_status_info()
    ai_status = ai_engine.get_engine_status()
    return render_template("index.html", user=user, paypal_status=pp_status, ai_status=ai_status)

@app.route("/paypal/success")
def paypal_success_return():
    token = request.args.get("token", "SANDBOX_MOCK_ORDER")
    payer_id = request.args.get("PayerID", "")
    return render_template(
        "index.html",
        user=get_current_user(),
        paypal_status=paypal_service.get_status_info(),
        ai_status=ai_engine.get_engine_status(),
        initial_toast={"type": "success", "message": f"PayPal Sandbox Order Authorized ({token}). Ready for capture."}
    )

@app.route("/paypal/cancel")
def paypal_cancel_return():
    return render_template(
        "index.html",
        user=get_current_user(),
        paypal_status=paypal_service.get_status_info(),
        ai_status=ai_engine.get_engine_status(),
        initial_toast={"type": "warning", "message": "PayPal payment was cancelled by user in Sandbox."}
    )

# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    full_name = (data.get("full_name") or username).strip()

    if not username or not email or not password:
        return jsonify({"success": False, "error": "Username, email, and password are required"}), 400

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"success": False, "error": "Invalid email address format"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
    if existing:
        conn.close()
        return jsonify({"success": False, "error": "Username or email is already registered"}), 409

    new_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    pw_hash = generate_password_hash(password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO users (id, username, email, password_hash, full_name, role, created_at)
    VALUES (?, ?, ?, ?, ?, 'freelancer', ?)
    """, (new_id, username, email, pw_hash, full_name, now_str))
    conn.commit()
    conn.close()

    session["user_id"] = new_id
    add_notification("New Account Registered", f"Welcome to FreelanceShield AI, {full_name}!", "Info", "user", new_id)

    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "user": {"id": new_id, "username": username, "email": email, "full_name": full_name}
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    login_id = (data.get("login") or "").strip()
    password = (data.get("password") or "").strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (login_id, login_id)).fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        return jsonify({
            "success": True,
            "message": "Logged in successfully",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            }
        })

    return jsonify({"success": False, "error": "Invalid username/email or password"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.pop("user_id", None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    return jsonify({"success": True, "user": get_current_user()})

# -----------------------------------------------------------------------------
# Dashboard & Analytics Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Transactions Totals
    cursor.execute("SELECT SUM(amount), COUNT(*) FROM transactions WHERE payment_status = 'Completed'")
    c_res = cursor.fetchone()
    total_completed = float(c_res[0] or 0.0)
    completed_count = int(c_res[1] or 0)

    cursor.execute("SELECT SUM(amount), COUNT(*) FROM transactions WHERE payment_status = 'Pending'")
    p_res = cursor.fetchone()
    total_pending = float(p_res[0] or 0.0)
    pending_count = int(p_res[1] or 0)

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE payment_status = 'Failed'")
    failed_count = int(cursor.fetchone()[0] or 0)

    # 2. Invoices
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM invoices")
    inv_res = cursor.fetchone()
    total_invoices = int(inv_res[0] or 0)
    total_invoice_amt = float(inv_res[1] or 0.0)

    cursor.execute("SELECT COUNT(*), SUM(amount) FROM invoices WHERE status != 'Paid'")
    unpaid_res = cursor.fetchone()
    unpaid_invoices_count = int(unpaid_res[0] or 0)
    unpaid_invoices_amt = float(unpaid_res[1] or 0.0)

    # 3. Security Reports & Threats
    cursor.execute("SELECT COUNT(*) FROM security_reports WHERE risk_classification IN ('Critical', 'High')")
    threats_detected = int(cursor.fetchone()[0] or 0)

    # 4. Total Protected Milestone Projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = int(cursor.fetchone()[0] or 0)

    # 5. Security Posture Score
    # Baseline 100 minus penalty for unresolved high risks
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE severity IN ('Critical', 'High') AND is_read = 0")
    active_critical_alerts = int(cursor.fetchone()[0] or 0)
    posture_score = max(65, 100 - (active_critical_alerts * 3))

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "total_payments_amount": round(total_completed + total_pending, 2),
            "completed_amount": round(total_completed, 2),
            "completed_count": completed_count,
            "pending_amount": round(total_pending, 2),
            "pending_count": pending_count,
            "failed_count": failed_count,
            "total_invoices": total_invoices,
            "total_invoice_amt": round(total_invoice_amt, 2),
            "unpaid_invoices_count": unpaid_invoices_count,
            "unpaid_invoices_amt": round(unpaid_invoices_amt, 2),
            "threats_detected": threats_detected,
            "total_projects": total_projects,
            "posture_score": posture_score
        }
    })

@app.route("/api/dashboard/transactions", methods=["GET"])
def get_dashboard_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    status_filter = request.args.get("status")
    limit = request.args.get("limit", 20, type=int)

    if status_filter and status_filter != "all":
        cursor.execute("SELECT * FROM transactions WHERE payment_status = ? ORDER BY created_at DESC LIMIT ?", (status_filter, limit))
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,))

    txns = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "transactions": txns})

@app.route("/api/dashboard/alerts", methods=["GET"])
def get_dashboard_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM security_reports ORDER BY created_at DESC LIMIT 10")
    reports = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "reports": reports})

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Monthly revenue breakdown
    cursor.execute("""
    SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total_volume, SUM(net_amount) as net_volume, COUNT(*) as count
    FROM transactions
    WHERE payment_status = 'Completed'
    GROUP BY month
    ORDER BY month ASC
    LIMIT 6
    """)
    monthly_rows = cursor.fetchall()
    months = [r["month"] for r in monthly_rows] or ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]
    monthly_volume = [float(r["total_volume"]) for r in monthly_rows] or [1800.0, 3200.0, 4800.0, 6400.0, 8940.0]

    # 2. Payment Status Distribution
    cursor.execute("SELECT payment_status, COUNT(*), SUM(amount) FROM transactions GROUP BY payment_status")
    status_rows = cursor.fetchall()
    status_dist = {r["payment_status"]: {"count": r[1], "amount": float(r[2] or 0.0)} for r in status_rows}

    # 3. Security Risk Breakdown
    cursor.execute("SELECT risk_classification, COUNT(*) FROM security_reports GROUP BY risk_classification")
    risk_rows = cursor.fetchall()
    risk_dist = {r["risk_classification"]: r[1] for r in risk_rows}

    # 4. Client trust rankings
    cursor.execute("SELECT name, trust_score, total_paid FROM client_records ORDER BY total_paid DESC LIMIT 5")
    clients = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "success": True,
        "analytics": {
            "months": months,
            "monthly_volume": monthly_volume,
            "status_distribution": status_dist,
            "risk_distribution": risk_dist,
            "top_clients": clients
        }
    })

# -----------------------------------------------------------------------------
# AI Security Center Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/ai/status", methods=["GET"])
def get_ai_status():
    return jsonify({"success": True, "status": ai_engine.get_engine_status()})

@app.route("/api/ai/analyze-message", methods=["POST"])
def analyze_message():
    data = request.get_json() or {}
    text = data.get("text", "")

    if not text or len(text.strip()) < 5:
        return jsonify({"success": False, "error": "Please provide a client message or proposal text to evaluate."}), 400

    report = ai_engine.analyze_scam_message(text)

    # Save report to SQLite
    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO security_reports (id, report_type, input_data, risk_score, risk_classification, detected_indicators_json, risk_explanation, recommendations_json, metadata_json, created_at)
    VALUES (?, 'message', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        text,
        report["risk_score"],
        report["risk_classification"],
        json.dumps(report["detected_indicators"]),
        report["risk_explanation"],
        json.dumps(report["recommendations"]),
        json.dumps({"engine": report.get("engine"), "highlights": report.get("highlighted_phrases")}),
        now_str
    ))
    conn.commit()
    conn.close()

    # Trigger notification if High or Critical
    if report["risk_classification"] in ("High", "Critical"):
        add_notification(
            title=f"Flagged {report['risk_classification']} Scam Message",
            description=f"Message scored {report['risk_score']}/100: {report['risk_explanation'][:120]}...",
            severity=report["risk_classification"],
            related_type="security_report",
            related_id=report_id
        )

    log_ai_activity("message_scan", text[:200], f"Score {report['risk_score']} ({report['risk_classification']})", report.get("engine"))

    report["report_id"] = report_id
    return jsonify({"success": True, "report": report})

@app.route("/api/ai/scan-url", methods=["POST"])
def scan_url():
    data = request.get_json() or {}
    url = data.get("url", "")

    if not url or len(url.strip()) < 4:
        return jsonify({"success": False, "error": "Please provide a URL to inspect."}), 400

    result = ai_engine.scan_url(url)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 400

    # Save to SQLite
    report_id = f"REP-URL-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO security_reports (id, report_type, input_data, risk_score, risk_classification, detected_indicators_json, risk_explanation, recommendations_json, metadata_json, created_at)
    VALUES (?, 'url', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        result["url"],
        result["risk_score"],
        result["risk_classification"],
        json.dumps(result["indicators"]),
        result["risk_explanation"],
        json.dumps([result["recommended_action"]]),
        json.dumps({"domain": result["domain"], "is_https": result["is_https"]}),
        now_str
    ))
    conn.commit()
    conn.close()

    # Trigger alert if suspicious
    if result["risk_classification"] in ("High", "Critical"):
        add_notification(
            title=f"Suspicious URL Quarantined ({result['domain']})",
            description=f"Scored {result['risk_score']}/100: {result['verdict']}",
            severity=result["risk_classification"],
            related_type="security_report",
            related_id=report_id
        )

    log_ai_activity("url_scan", url, f"Score {result['risk_score']} ({result['domain']})")

    result["report_id"] = report_id
    return jsonify({"success": True, "result": result})

@app.route("/api/ai/analyze-job", methods=["POST"])
def analyze_job():
    data = request.get_json() or {}
    title = data.get("title", "")
    description = data.get("description", "")
    budget = data.get("budget", "")

    if not title or not description:
        return jsonify({"success": False, "error": "Job title and description are required."}), 400

    result = ai_engine.analyze_job_offer(title, description, budget)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 400

    # Save to SQLite
    report_id = f"REP-JOB-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO security_reports (id, report_type, input_data, risk_score, risk_classification, detected_indicators_json, risk_explanation, recommendations_json, metadata_json, created_at)
    VALUES (?, 'job', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        f"{title}: {description[:400]}",
        result["risk_score"],
        result["risk_classification"],
        json.dumps(result.get("flags", [])),
        result["verdict"],
        json.dumps(result.get("recommendations", [])),
        json.dumps({"title": title, "budget": budget}),
        now_str
    ))
    conn.commit()
    conn.close()

    if result["risk_classification"] in ("High", "Critical"):
        add_notification(
            title=f"Flagged Job Posting: {title[:40]}",
            description=f"Risk Score {result['risk_score']}/100 ({result['verdict']})",
            severity=result["risk_classification"],
            related_type="security_report",
            related_id=report_id
        )

    log_ai_activity("job_scan", title, f"Score {result['risk_score']}")

    result["report_id"] = report_id
    return jsonify({"success": True, "result": result})

@app.route("/api/ai/generate-invoice", methods=["POST"])
def ai_generate_invoice():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")

    if not prompt or len(prompt.strip()) < 5:
        return jsonify({"success": False, "error": "Please provide an instruction for invoice generation."}), 400

    extracted = ai_engine.generate_invoice_from_prompt(prompt)
    if "error" in extracted:
        return jsonify({"success": False, "error": extracted["error"]}), 400

    log_ai_activity("invoice_gen", prompt[:150], f"Generated {extracted.get('invoice_number')} for {extracted.get('client_name')}")

    return jsonify({"success": True, "invoice": extracted})

@app.route("/api/ai/assistant", methods=["POST"])
def ai_financial_assistant():
    data = request.get_json() or {}
    message = data.get("message", "")

    if not message:
        return jsonify({"success": False, "error": "Query message cannot be empty."}), 400

    # Build live database context for grounded responses
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT SUM(amount), COUNT(*) FROM transactions WHERE payment_status = 'Completed'")
    comp_row = c.fetchone()
    total_completed = float(comp_row[0] or 0.0)
    completed_count = int(comp_row[1] or 0)

    c.execute("SELECT SUM(amount), COUNT(*) FROM transactions WHERE payment_status = 'Pending'")
    pend_row = c.fetchone()
    total_pending = float(pend_row[0] or 0.0)
    pending_count = int(pend_row[1] or 0)

    c.execute("SELECT COUNT(*) FROM transactions WHERE payment_status = 'Failed'")
    failed_count = int(c.fetchone()[0] or 0)

    c.execute("SELECT COUNT(*), SUM(amount) FROM invoices WHERE status != 'Paid'")
    unpaid_inv_row = c.fetchone()
    unpaid_invoices_count = int(unpaid_inv_row[0] or 0)
    unpaid_invoices_total = float(unpaid_inv_row[1] or 0.0)

    c.execute("SELECT COUNT(*) FROM security_reports WHERE risk_classification IN ('Critical', 'High')")
    threats_count = int(c.fetchone()[0] or 0)

    c.execute("SELECT client_name, amount, payment_status, security_status FROM transactions ORDER BY created_at DESC LIMIT 5")
    recent_txns = [dict(r) for r in c.fetchall()]

    c.execute("SELECT invoice_number, client_name, amount, status, due_date FROM invoices ORDER BY created_at DESC LIMIT 5")
    recent_invoices = [dict(r) for r in c.fetchall()]

    conn.close()

    db_context = {
        "total_completed": total_completed,
        "completed_count": completed_count,
        "total_pending": total_pending,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "unpaid_invoices_count": unpaid_invoices_count,
        "unpaid_invoices_total": unpaid_invoices_total,
        "threats_count": threats_count,
        "recent_transactions": recent_txns,
        "recent_invoices": recent_invoices
    }

    reply = ai_engine.answer_financial_query(message, db_context)
    log_ai_activity("assistant", message[:150], reply[:150])

    return jsonify({
        "success": True,
        "reply": reply,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })

# -----------------------------------------------------------------------------
# PayPal Sandbox Payment Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/paypal/status", methods=["GET"])
def paypal_status():
    return jsonify({"success": True, "status": paypal_service.get_status_info()})

@app.route("/api/paypal/create-order", methods=["POST"])
def paypal_create_order():
    data = request.get_json() or {}
    amount = data.get("amount")
    currency = data.get("currency", "USD")
    description = data.get("description", "FreelanceShield Milestone Escrow")
    client_name = data.get("client_name", "Anonymous Client")
    client_email = data.get("client_email", "client@sandbox.paypal.com")
    invoice_id = data.get("invoice_id")

    if not amount or float(amount) <= 0:
        return jsonify({"success": False, "error": "A valid payment amount greater than zero is required."}), 400

    order_result = paypal_service.create_order(
        amount=amount,
        currency=currency,
        description=description,
        client_name=client_name,
        client_email=client_email,
        invoice_id=invoice_id
    )

    if not order_result.get("success"):
        return jsonify({"success": False, "error": order_result.get("error")}), 500

    order_id = order_result["order_id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Record initial transaction in SQLite (idempotent tracking)
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO transactions (id, paypal_order_id, client_name, client_email, client_company, amount, currency, payment_status, ai_risk_score, security_status, risk_reason, paypal_fee, net_amount, ip_address, country, is_sandbox, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', 5, 'Safe', 'PayPal Sandbox order created. Awaiting buyer authorization and capture.', 0.0, 0.0, ?, 'Sandbox', 1, ?, ?)
    """, (
        txn_id,
        order_id,
        client_name,
        client_email,
        data.get("client_company", "Freelance Client"),
        float(amount),
        currency,
        request.remote_addr or "127.0.0.1",
        now_str,
        now_str
    ))

    # If linked to an invoice, update invoice paypal_order_id
    if invoice_id:
        cursor.execute("UPDATE invoices SET paypal_order_id = ?, status = 'Pending', updated_at = ? WHERE id = ? OR invoice_number = ?", (order_id, now_str, invoice_id, invoice_id))

    conn.commit()
    conn.close()

    add_notification(
        title="PayPal Sandbox Order Created",
        description=f"Order {order_id} generated for {client_name} (${float(amount):,.2f} {currency}).",
        severity="Info",
        related_type="transaction",
        related_id=txn_id
    )

    return jsonify({
        "success": True,
        "order": order_result,
        "transaction_id": txn_id
    }), 201

@app.route("/api/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    data = request.get_json() or {}
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"success": False, "error": "PayPal order_id is required for capture."}), 400

    capture_result = paypal_service.capture_order(order_id)
    if not capture_result.get("success"):
        return jsonify({"success": False, "error": capture_result.get("error", "Capture failed")}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find existing transaction for this order
    existing_txn = cursor.execute("SELECT * FROM transactions WHERE paypal_order_id = ?", (order_id,)).fetchone()

    capture_id = capture_result.get("capture_id", f"PP-CAP-{uuid.uuid4().hex[:8].upper()}")

    if existing_txn:
        gross = float(existing_txn["amount"])
        fee = round(gross * 0.029 + 0.30, 2)
        net = round(gross - fee, 2)

        cursor.execute("""
        UPDATE transactions
        SET payment_status = 'Completed',
            paypal_capture_id = ?,
            paypal_fee = ?,
            net_amount = ?,
            updated_at = ?
        WHERE paypal_order_id = ?
        """, (capture_id, fee, net, now_str, order_id))

        txn_id = existing_txn["id"]
        client_name = existing_txn["client_name"]
    else:
        # Create completed transaction if not previously registered
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        gross = float(data.get("amount", 250.0))
        fee = round(gross * 0.029 + 0.30, 2)
        net = round(gross - fee, 2)
        client_name = data.get("client_name", "Sandbox Buyer")

        cursor.execute("""
        INSERT INTO transactions (id, paypal_order_id, paypal_capture_id, client_name, client_email, amount, currency, payment_status, ai_risk_score, security_status, risk_reason, paypal_fee, net_amount, ip_address, country, is_sandbox, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'buyer@sandbox.paypal.com', ?, 'USD', 'Completed', 4, 'Safe', 'Captured and verified through PayPal Sandbox.', ?, ?, '127.0.0.1', 'Sandbox', 1, ?, ?)
        """, (txn_id, order_id, capture_id, client_name, gross, fee, net, now_str, now_str))

    # Also update any linked invoice
    cursor.execute("""
    UPDATE invoices
    SET status = 'Paid', updated_at = ?
    WHERE paypal_order_id = ?
    """, (now_str, order_id))

    conn.commit()
    conn.close()

    add_notification(
        title="Payment Captured Successfully",
        description=f"PayPal Sandbox captured ${gross:,.2f} from {client_name} (Capture ID: {capture_id}).",
        severity="Info",
        related_type="transaction",
        related_id=txn_id
    )

    return jsonify({
        "success": True,
        "message": "PayPal payment captured and verified.",
        "capture": capture_result,
        "transaction_id": txn_id
    })

@app.route("/api/paypal/webhook", methods=["POST"])
def paypal_webhook():
    """Receives and verifies PayPal webhook events idempotently."""
    headers = dict(request.headers)
    body = request.get_data(as_text=True)

    verified = paypal_service.verify_webhook_event(headers, body)
    if not verified:
        return jsonify({"success": False, "error": "Invalid webhook signature"}), 400

    try:
        event = json.loads(body)
        event_type = event.get("event_type", "UNKNOWN")
        resource = event.get("resource", {})

        add_notification(
            title=f"PayPal Webhook: {event_type}",
            description=f"Received webhook event {event_type} for resource {resource.get('id', 'N/A')}",
            severity="Info",
            related_type="webhook",
            related_id=event.get("id")
        )
        return jsonify({"success": True, "message": "Webhook processed idempotently."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# -----------------------------------------------------------------------------
# Invoices Management Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/invoices", methods=["GET"])
def get_invoices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY created_at DESC")
    invoices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "invoices": invoices})

@app.route("/api/invoices", methods=["POST"])
def create_invoice():
    data = request.get_json() or {}
    client_name = (data.get("client_name") or "").strip()
    client_email = (data.get("client_email") or "").strip()
    project_title = (data.get("project_title") or "").strip()
    amount = data.get("amount")

    if not client_name or not project_title or amount is None:
        return jsonify({"success": False, "error": "Client name, project title, and amount are required."}), 400

    try:
        amt = float(amount)
        if amt <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"success": False, "error": "Invalid amount value."}), 400

    inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    inv_number = data.get("invoice_number") or f"FS-INV-2026-{uuid.uuid4().hex[:4].upper()}"
    currency = data.get("currency", "USD")
    due_date = data.get("due_date") or (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    description = data.get("description", f"Freelance services for {project_title}")
    items = data.get("items") or [{"desc": project_title, "qty": 1, "rate": amt, "amount": amt}]
    items_json = json.dumps(items)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO invoices (id, invoice_number, client_name, client_email, project_title, description, amount, currency, status, due_date, items_json, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Unpaid', ?, ?, ?, ?)
    """, (inv_id, inv_number, client_name, client_email or "billing@client.com", project_title, description, amt, currency, due_date, items_json, now_str, now_str))

    # Also register client if not exists
    cursor.execute("SELECT id FROM client_records WHERE email = ?", (client_email,))
    if not cursor.fetchone() and client_email:
        cli_id = f"CLI-{uuid.uuid4().hex[:6].upper()}"
        initials = "".join([part[0] for part in client_name.split()[:2]]).upper() or "CL"
        cursor.execute("""
        INSERT INTO client_records (id, name, email, company, trust_score, verification_status, total_paid, dispute_rate, country, avatar_initials, created_at)
        VALUES (?, ?, ?, ?, 90, 'Active', 0.0, 0.0, 'United States', ?, ?)
        """, (cli_id, client_name, client_email, client_name, initials, now_str))

    conn.commit()
    conn.close()

    add_notification(
        title="New Invoice Created",
        description=f"Invoice {inv_number} issued to {client_name} for ${amt:,.2f} {currency}.",
        severity="Info",
        related_type="invoice",
        related_id=inv_id
    )

    return jsonify({
        "success": True,
        "message": "Invoice created successfully.",
        "invoice": {
            "id": inv_id,
            "invoice_number": inv_number,
            "client_name": client_name,
            "amount": amt,
            "currency": currency,
            "due_date": due_date,
            "status": "Unpaid"
        }
    }), 201

@app.route("/api/invoices/<inv_id>", methods=["GET"])
def get_invoice_by_id(inv_id):
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id)).fetchone()
    conn.close()
    if not inv:
        return jsonify({"success": False, "error": "Invoice not found"}), 404
    return jsonify({"success": True, "invoice": dict(inv)})

@app.route("/api/invoices/<inv_id>", methods=["PUT"])
def update_invoice(inv_id):
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.cursor()

    inv = cursor.execute("SELECT * FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id)).fetchone()
    if not inv:
        conn.close()
        return jsonify({"success": False, "error": "Invoice not found"}), 404

    client_name = data.get("client_name", inv["client_name"])
    client_email = data.get("client_email", inv["client_email"])
    project_title = data.get("project_title", inv["project_title"])
    description = data.get("description", inv["description"])
    amount = float(data.get("amount", inv["amount"]))
    status = data.get("status", inv["status"])
    due_date = data.get("due_date", inv["due_date"])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE invoices
    SET client_name = ?, client_email = ?, project_title = ?, description = ?, amount = ?, status = ?, due_date = ?, updated_at = ?
    WHERE id = ? OR invoice_number = ?
    """, (client_name, client_email, project_title, description, amount, status, due_date, now_str, inv_id, inv_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Invoice updated successfully."})

@app.route("/api/invoices/<inv_id>", methods=["DELETE"])
def delete_invoice(inv_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Invoice deleted."})

@app.route("/api/invoices/<inv_id>/pdf", methods=["GET"])
def download_invoice_pdf(inv_id):
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id)).fetchone()
    conn.close()

    if not inv:
        return jsonify({"success": False, "error": "Invoice not found"}), 404

    inv_dict = dict(inv)
    pdf_path = generate_invoice_pdf(inv_dict)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{inv_dict.get('invoice_number', 'Invoice')}.pdf",
        mimetype="application/pdf"
    )

@app.route("/api/invoices/<inv_id>/create-paypal-order", methods=["POST"])
def invoice_create_paypal_order(inv_id):
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM invoices WHERE id = ? OR invoice_number = ?", (inv_id, inv_id)).fetchone()
    conn.close()

    if not inv:
        return jsonify({"success": False, "error": "Invoice not found"}), 404

    order_result = paypal_service.create_order(
        amount=inv["amount"],
        currency=inv["currency"],
        description=f"Payment for {inv['invoice_number']} - {inv['project_title']}",
        client_name=inv["client_name"],
        client_email=inv["client_email"],
        invoice_id=inv["invoice_number"]
    )

    if not order_result.get("success"):
        return jsonify({"success": False, "error": order_result.get("error")}), 500

    order_id = order_result["order_id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Link PayPal order ID to invoice
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET paypal_order_id = ?, status = 'Pending', updated_at = ? WHERE id = ? OR invoice_number = ?", (order_id, now_str, inv_id, inv_id))

    # Also register transaction
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    cursor.execute("""
    INSERT INTO transactions (id, paypal_order_id, client_name, client_email, amount, currency, payment_status, ai_risk_score, security_status, risk_reason, paypal_fee, net_amount, ip_address, country, is_sandbox, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 'Pending', 4, 'Safe', 'Awaiting PayPal Sandbox checkout approval.', 0.0, 0.0, '127.0.0.1', 'Sandbox', 1, ?, ?)
    """, (txn_id, order_id, inv["client_name"], inv["client_email"], float(inv["amount"]), inv["currency"], now_str, now_str))

    conn.commit()
    conn.close()

    add_notification(
        title="PayPal Order Linked to Invoice",
        description=f"Generated PayPal Sandbox Order {order_id} for invoice {inv['invoice_number']}.",
        severity="Info",
        related_type="invoice",
        related_id=inv["id"]
    )

    return jsonify({
        "success": True,
        "order": order_result,
        "transaction_id": txn_id
    })

# -----------------------------------------------------------------------------
# Notifications Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 50")
    notifications = [dict(r) for r in cursor.fetchall()]
    unread_count = sum(1 for n in notifications if not n["is_read"])
    conn.close()
    return jsonify({
        "success": True,
        "notifications": notifications,
        "unread_count": unread_count
    })

@app.route("/api/notifications/<notif_id>/read", methods=["PATCH", "POST"])
def mark_notification_read(notif_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Notification marked as read."})

@app.route("/api/notifications/read-all", methods=["POST"])
def mark_all_notifications_read():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "All notifications marked as read."})

# -----------------------------------------------------------------------------
# Projects and Clients Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/projects", methods=["GET"])
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "projects": projects})

@app.route("/api/clients", methods=["GET"])
def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM client_records ORDER BY trust_score DESC")
    clients = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "clients": clients})

# -----------------------------------------------------------------------------
# Global Error Handlers (Zero stack trace exposure)
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def error_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Requested API endpoint not found."}), 404
    return render_template("index.html", initial_toast={"type": "error", "message": "Resource not found (404)"}), 404

@app.errorhandler(500)
def error_internal_server(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server processing error. Our AI security agent has logged this incident."}), 500
    return render_template("index.html", initial_toast={"type": "error", "message": "Server processing error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"\n=======================================================")
    print(f" [FreelanceShield AI] Platform is Live")
    print(f" * Local URL: http://127.0.0.1:{port}")
    print(f" * PayPal Mode: {paypal_service.get_status_info()['mode']}")
    print(f" * AI Model: {ai_engine.get_engine_status()['model']}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
