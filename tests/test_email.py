import pytest

from app.models import email
from app.models.email import EmailError


@pytest.fixture()
def resend_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(email.Config, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(email.resend.Emails, "send", lambda params: calls.append(params) or {"id": "email-1"})
    return calls


def test_send_email_without_attachments_omits_the_field(resend_calls):
    assert email.send_email("a@example.com", "Asunto", "<p>hola</p>") == "email-1"
    assert "attachments" not in resend_calls[0]
    assert resend_calls[0]["to"] == ["a@example.com"]


def test_send_email_forwards_attachments(resend_calls):
    attachment = {"filename": "grafico.png", "content": "aGk=", "content_id": "chart-x"}
    email.send_email("a@example.com", "Asunto", "<img src='cid:chart-x'>", attachments=[attachment])
    assert resend_calls[0]["attachments"] == [attachment]


def test_send_email_requires_api_key(monkeypatch):
    monkeypatch.setattr(email.Config, "RESEND_API_KEY", "")
    with pytest.raises(EmailError):
        email.send_email("a@example.com", "Asunto", "<p>hola</p>")
