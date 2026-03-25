import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_email(subject: str, body: str):
    """Send a plain text email alert."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.ALERT_EMAIL_FROM
        msg["To"] = settings.ALERT_EMAIL_TO
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.ALERT_EMAIL_FROM, settings.ALERT_EMAIL_PASSWORD)
            server.sendmail(
                settings.ALERT_EMAIL_FROM,
                settings.ALERT_EMAIL_TO,
                msg.as_string()
            )
        print(f"✅ Email sent: {subject}")

    except Exception as e:
        print(f"❌ Email failed: {e}")


def send_anomaly_alert(anomalies: list):
    """Send an alert email listing all flagged anomalies."""
    if not anomalies:
        return

    lines = ["⚠️ FinSight Anomaly Alert\n"]
    lines.append(f"{len(anomalies)} unusual transaction(s) detected:\n")

    for t in anomalies:
        lines.append(f"  • {t.date} | {t.description} | ₹{t.amount} | Score: {t.anomaly_score}")

    lines.append("\nLog in to review these transactions.")
    body = "\n".join(lines)

    send_email("⚠️ FinSight: Anomalies Detected", body)


def send_weekly_report_email(report: dict):
    """Send the weekly report as an email."""
    s = report["summary"]
    v = report["vs_last_week"]
    period = report["report_period"]

    lines = [
        f"📊 FinSight Weekly Report",
        f"Period: {period['from']} to {period['to']}",
        f"",
        f"💰 Total Spent: ₹{s['total_spent']}",
        f"💵 Total Income: ₹{s['total_income']}",
        f"📈 Net: ₹{s['net']}",
        f"🔢 Transactions: {s['total_transactions']}",
        f"🚨 Anomalies: {s['anomalies_flagged']}",
        f"",
        f"vs Last Week: {v['verdict']}",
        f"",
        f"Top Categories:",
    ]

    for cat in report["top_categories"]:
        lines.append(f"  • {cat['category']}: ₹{cat['total_spent']}")

    if report["biggest_expense"]:
        b = report["biggest_expense"]
        lines.append(f"\nBiggest Expense: {b['description']} — ₹{abs(b['amount'])}")

    body = "\n".join(lines)
    send_email(f"📊 FinSight Weekly Report ({period['from']})", body)