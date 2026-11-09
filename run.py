"""
FreelanceShield AI - Application Runner
Launches the Flask server with environment variable validation and clear console telemetry.
"""

import os
from dotenv import load_dotenv
from app import app, init_db, paypal_service, ai_engine

load_dotenv()

if __name__ == "__main__":
    init_db()

    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")

    pp_info = paypal_service.get_status_info()
    ai_info = ai_engine.get_engine_status()

    print("\n=================================================================")
    print(" [FREELANCESHIELD AI] CYBERSECURITY & PAYMENT AUTOMATION")
    print("=================================================================")
    print(f" * Local Web URL : http://127.0.0.1:{port}")
    print(f" * PayPal Status : {pp_info['mode']}")
    print(f" * AI Engine     : {ai_info['model']}")
    print(f" * Database      : SQLite (freelanceshield.db)")
    print("=================================================================\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
