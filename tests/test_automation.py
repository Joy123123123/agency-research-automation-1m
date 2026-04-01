"""
Tests for Automation Modules
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.automation.follow_up import FollowUpManager
from src.automation.email_sender import EmailSender, _html_to_text


class TestFollowUpManager:
    def setup_method(self):
        # Use temp file for testing
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmpfile.write(b"{}")
        self.tmpfile.close()
        self.manager = FollowUpManager(tracking_file=self.tmpfile.name)

    def teardown_method(self):
        os.unlink(self.tmpfile.name)

    def test_enqueue_lead(self):
        self.manager.enqueue_lead("test@test.com", "Test Business", {"niche": "restaurant"})
        assert "test@test.com" in self.manager.data
        assert self.manager.data["test@test.com"]["status"] == "active"

    def test_mark_replied(self):
        self.manager.enqueue_lead("test@test.com", "Test", {})
        self.manager.mark_replied("test@test.com")
        assert self.manager.data["test@test.com"]["replied"] is True
        assert self.manager.data["test@test.com"]["status"] == "replied"

    def test_unsubscribe(self):
        self.manager.enqueue_lead("test@test.com", "Test", {})
        self.manager.unsubscribe("test@test.com")
        assert self.manager.data["test@test.com"]["unsubscribed"] is True

    def test_get_due_emails(self):
        self.manager.enqueue_lead("due@test.com", "Due Business", {})
        due = self.manager.get_due_emails()
        assert any(d["email"] == "due@test.com" for d in due)

    def test_replied_not_in_due(self):
        self.manager.enqueue_lead("replied@test.com", "Replied", {})
        self.manager.mark_replied("replied@test.com")
        due = self.manager.get_due_emails()
        assert not any(d["email"] == "replied@test.com" for d in due)


class TestEmailSender:
    def setup_method(self):
        # No API key — tests fallback behavior
        self.sender = EmailSender("", "test@test.com", "Test Sender")

    def test_send_without_credentials(self):
        """When no credentials are configured, email is skipped (not sent)."""
        result = self.sender.send_single(
            to_email="lead@test.com",
            to_name="Lead",
            subject="Test",
            html_content="<p>Hello</p>"
        )
        # "skipped" means no backend is configured — not an error, just no-op
        assert result.status in ("skipped", "failed")
        assert result.error is not None
        assert "not configured" in result.error.lower() or "credential" in result.error.lower()

    def test_not_configured_when_no_keys(self):
        """EmailSender reports unconfigured when neither SendGrid nor SMTP keys provided."""
        assert not self.sender.is_configured()

    def test_html_to_text(self):
        html = "<p>Hello <b>World</b></p>"
        text = _html_to_text(html)
        assert "Hello" in text
        assert "World" in text
        assert "<" not in text
