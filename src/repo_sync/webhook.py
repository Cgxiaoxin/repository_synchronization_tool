"""Webhook server for real-time synchronization."""

import logging
import hmac
import hashlib
from typing import Optional

from flask import Flask, request, jsonify

from .config import ConfigManager
from .sync_engine import SyncEngine

logger = logging.getLogger(__name__)

app = Flask(__name__)
sync_engine: Optional[SyncEngine] = None
webhook_secret: str = ""


def create_app(config_path: Optional[str] = None) -> Flask:
    """Create Flask application."""
    global sync_engine, webhook_secret
    
    config_manager = ConfigManager(config_path)
    config = config_manager.load()
    sync_engine = SyncEngine(config_path)
    webhook_secret = config.webhook.secret

    @app.route("/webhook", methods=["POST"])
    def handle_webhook():
        """Handle webhook requests."""
        if webhook_secret:
            signature = request.headers.get("X-Hub-Signature-256")
            if not _verify_signature(request.data, webhook_secret, signature):
                return jsonify({"error": "Invalid signature"}), 401

        payload = request.json
        if not payload:
            return jsonify({"error": "No payload"}), 400

        event = request.headers.get("X-GitHub-Event", "push")
        
        if event == "push":
            repo_name = payload.get("repository", {}).get("name")
            if repo_name:
                logger.info(f"Received push event for repository: {repo_name}")
                results = sync_engine.sync_by_name(repo_name)
                return jsonify({
                    "status": "completed",
                    "results": [{"success": r.success, "message": r.message} for r in results]
                })

        return jsonify({"status": "ignored", "event": event})

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    return app


def _verify_signature(payload: bytes, secret: str, signature: Optional[str]) -> bool:
    """Verify webhook signature."""
    if not signature:
        return False
    
    if not signature.startswith("sha256="):
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)


def run_webhook_server(host: str = "0.0.0.0", port: int = 8080, config_path: Optional[str] = None):
    """Run webhook server."""
    app_instance = create_app(config_path)
    app_instance.run(host=host, port=port, threaded=True)
