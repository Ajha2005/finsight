from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.services.report import generate_weekly_report
from app.services.email import send_weekly_report_email
from app.models.transaction import Transaction


def run_weekly_report():
    print("⏰ Running scheduled weekly report...")
    db = SessionLocal()
    try:
        from datetime import date, timedelta
        from app.models.transaction import Transaction

        # Check if any transactions were uploaded this week
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        recent = db.query(Transaction).filter(
            Transaction.uploaded_at >= start_of_week
        ).first()

        if not recent:
            print("⏭️  No new transactions this week, skipping report.")
            return

        report = generate_weekly_report(db, weeks_ago=1)
        send_weekly_report_email(report)
        print("✅ Weekly report sent.")
    except Exception as e:
        print(f"❌ Scheduled report failed: {e}")
    finally:
        db.close()


def run_anomaly_check():
    """Job that runs daily — checks for anomalies and sends alert if any found."""
    print("⏰ Running anomaly check...")
    db = SessionLocal()
    try:
        anomalies = db.query(Transaction).filter(Transaction.is_anomaly == 1).all()
        if anomalies:
            from app.services.email import send_anomaly_alert
            send_anomaly_alert(anomalies)
            print(f"✅ Anomaly alert sent for {len(anomalies)} transactions.")
        else:
            print("✅ No anomalies found.")
    except Exception as e:
        print(f"❌ Anomaly check failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler with all jobs."""
    scheduler = BackgroundScheduler()

    # Weekly report — every Monday at 8:00 AM
    scheduler.add_job(
        run_weekly_report,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_report",
        name="Weekly Financial Report"
    )

    # Anomaly check — every day at 9:00 AM
    scheduler.add_job(
        run_anomaly_check,
        CronTrigger(hour=9, minute=0),
        id="anomaly_check",
        name="Daily Anomaly Check"
    )

    scheduler.start()
    print("✅ Scheduler started. Jobs: weekly report (Mon 8am), anomaly check (daily 9am)")
    return scheduler
