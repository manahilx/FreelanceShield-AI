"""
FreelanceShield AI - Automated Integration & End-to-End Test Suite
Tests all REST endpoints, DB transactions, AI security analyzers, PDF creation, and PayPal Sandbox workflows.
"""

import unittest
import json
import os
from app import app, init_db, get_db_connection

class FreelanceShieldTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key-2026"
        self.client = self.app.test_client()
        init_db()

    def test_01_index_page(self):
        """Verify main landing and dashboard SPA renders."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FreelanceShield", response.data)

    def test_02_dashboard_stats(self):
        """Verify dashboard statistics API returns real database figures."""
        response = self.client.get("/api/dashboard/stats")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        stats = data["stats"]
        self.assertIn("completed_amount", stats)
        self.assertIn("pending_amount", stats)
        self.assertIn("threats_detected", stats)
        self.assertGreaterEqual(stats["completed_amount"], 0)

    def test_03_transactions_api(self):
        """Verify transactions listing and filtering."""
        response = self.client.get("/api/dashboard/transactions")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["transactions"], list)
        self.assertGreater(len(data["transactions"]), 0)

    def test_04_ai_scam_message_analysis(self):
        """Verify AI Scam Detector on high-risk overpayment input."""
        payload = {
            "text": "Hello, I will send you a cashier's check for $8,500. Please deposit it and wire the remaining $2,000 to my supplier on Telegram @vendor_fast."
        }
        response = self.client.post("/api/ai/analyze-message", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        report = data["report"]
        self.assertGreaterEqual(report["risk_score"], 70)
        self.assertIn(report["risk_classification"], ["High", "Critical"])
        self.assertGreater(len(report["detected_indicators"]), 0)

    def test_05_ai_url_scanner(self):
        """Verify Suspicious URL Scanner detects brand spoofing and deceptive TLD."""
        payload = {"url": "http://paypal.com.account-verify-milestone.top/login"}
        response = self.client.post("/api/ai/scan-url", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        result = data["result"]
        self.assertGreaterEqual(result["risk_score"], 75)
        self.assertEqual(result["risk_classification"], "Critical")
        self.assertFalse(result["is_https"])

    def test_06_ai_job_offer_analyzer(self):
        """Verify Freelance Job Offer Analyzer flags advance-fee schemes."""
        payload = {
            "title": "Data Entry Specialist ($90/hr)",
            "description": "Looking for typists. Must pay a refundable $150 onboarding kit fee to start. Reach out on WhatsApp.",
            "budget": "90/hr"
        }
        response = self.client.post("/api/ai/analyze-job", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["result"]["risk_score"], 70)

    def test_07_ai_invoice_generator(self):
        """Verify AI extraction from natural language invoice instruction."""
        payload = {
            "prompt": "Create an invoice for a $750 website development project for ABC Solutions due in 14 days"
        }
        response = self.client.post("/api/ai/generate-invoice", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        inv = data["invoice"]
        self.assertEqual(inv["amount"], 750.0)
        self.assertIn("ABC Solutions", inv["client_name"])
        self.assertEqual(inv["currency"], "USD")

    def test_08_invoice_crud_and_pdf(self):
        """Verify Invoice creation, retrieval, PDF generation, and deletion."""
        # 1. Create Invoice
        create_payload = {
            "client_name": "Zenith AI Corp",
            "client_email": "billing@zenith.ai",
            "project_title": "Security Engine Hardening",
            "amount": 950.00,
            "currency": "USD",
            "due_date": "2026-11-20"
        }
        res_create = self.client.post("/api/invoices", json=create_payload)
        self.assertEqual(res_create.status_code, 201)
        inv_data = res_create.get_json()["invoice"]
        inv_id = inv_data["id"]

        # 2. Get Invoice by ID
        res_get = self.client.get(f"/api/invoices/{inv_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()["invoice"]["amount"], 950.00)

        # 3. Download PDF
        res_pdf = self.client.get(f"/api/invoices/{inv_id}/pdf")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, "application/pdf")
        self.assertGreater(len(res_pdf.data), 1000)
        res_pdf.close()

        # 4. Clean up
        res_del = self.client.delete(f"/api/invoices/{inv_id}")
        self.assertEqual(res_del.status_code, 200)

    def test_09_paypal_sandbox_workflow(self):
        """Verify PayPal order creation and server-side capture verification."""
        # 1. Check Status
        status_res = self.client.get("/api/paypal/status")
        self.assertEqual(status_res.status_code, 200)
        self.assertTrue(status_res.get_json()["status"]["connected"])

        # 2. Create Order
        order_payload = {
            "amount": 300.00,
            "currency": "USD",
            "description": "Milestone Escrow Test",
            "client_name": "Sandbox Tester",
            "client_email": "buyer@sandbox.paypal.com"
        }
        res_order = self.client.post("/api/paypal/create-order", json=order_payload)
        self.assertEqual(res_order.status_code, 201)
        order_data = res_order.get_json()
        self.assertTrue(order_data["success"])
        order_id = order_data["order"]["order_id"]
        self.assertTrue(order_id.startswith("PP-ORD-"))

        # 3. Capture Order
        res_cap = self.client.post("/api/paypal/capture-order", json={"order_id": order_id, "amount": 300.00})
        self.assertEqual(res_cap.status_code, 200)
        cap_data = res_cap.get_json()
        self.assertTrue(cap_data["success"])
        self.assertEqual(cap_data["capture"]["status"], "COMPLETED")

    def test_10_ai_financial_assistant(self):
        """Verify AI assistant answers queries grounded in SQLite database."""
        payload = {"message": "How much money have I received?"}
        res = self.client.post("/api/ai/assistant", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("$", data["reply"])
        self.assertIn("completed", data["reply"].lower())

    def test_11_notifications_api(self):
        """Verify notifications retrieval and marking read."""
        res = self.client.get("/api/notifications")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["notifications"], list)

        # Mark all read
        res_read = self.client.post("/api/notifications/read-all")
        self.assertEqual(res_read.status_code, 200)

if __name__ == "__main__":
    unittest.main()
