import os
import json
import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from backend.emailer import (
    format_daily_report, format_html_report,
    format_weekly_report, format_weekly_html_report,
    send_email_report
)

logger = logging.getLogger("solar_app.scheduler")

_scheduler_instance = None
_scheduler_lock = threading.Lock()
_scheduler_started = False

def run_daily_report_job(stock_file_path: str):
    logger.info("Scheduled task triggered: daily stock report")
    if not os.path.exists(stock_file_path):
        logger.error(f"Stock file not found: {stock_file_path}")
        return
    try:
        with open(stock_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        products = data.get("products", [])
        transactions = data.get("transactions", [])
        config = data.get("config", {})

        email_result = send_email_report(
            config,
            format_daily_report(products, transactions),
            format_html_report(products, transactions)
        )
        if email_result.get("success"):
            logger.info("Daily email report sent successfully")
        else:
            logger.error(f"Daily email report failed: {email_result.get('error')}")

        try:
            from backend.whatsapp import send_daily_whatsapp_report
            wa_result = send_daily_whatsapp_report(config, products, transactions)
            if wa_result.get("success"):
                logger.info("Daily WhatsApp report sent successfully")
            else:
                logger.warning(f"Daily WhatsApp report not sent: {wa_result.get('error')}")
        except Exception as wa_e:
            logger.warning(f"Daily WhatsApp report skipped: {wa_e}")

    except Exception as e:
        logger.exception(f"Error in daily report job: {e}")

def run_weekly_report_job(stock_file_path: str):
    logger.info("Scheduled task triggered: weekly stock report")
    if not os.path.exists(stock_file_path):
        logger.error(f"Stock file not found: {stock_file_path}")
        return
    try:
        with open(stock_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        products = data.get("products", [])
        transactions = data.get("transactions", [])
        config = data.get("config", {})

        report_text, period = format_weekly_report(products, transactions)
        html_body = format_weekly_html_report(products, transactions)
        subject = f"Solar Store Weekly Report - {period}"

        email_result = send_email_report(config, report_text, html_body, subject=subject)
        if email_result.get("success"):
            logger.info("Weekly email report sent successfully")
        else:
            logger.error(f"Weekly email report failed: {email_result.get('error')}")

        try:
            from backend.whatsapp import send_daily_whatsapp_report
            wa_result = send_daily_whatsapp_report(config, products, transactions)
            if wa_result.get("success"):
                logger.info("Weekly WhatsApp report sent successfully")
            else:
                logger.warning(f"Weekly WhatsApp report not sent: {wa_result.get('error')}")
        except Exception as wa_e:
            logger.warning(f"Weekly WhatsApp report skipped: {wa_e}")

    except Exception as e:
        logger.exception(f"Error in weekly report job: {e}")

def init_scheduler(stock_file_path: str) -> BackgroundScheduler:
    global _scheduler_instance, _scheduler_started

    with _scheduler_lock:
        if _scheduler_instance is not None:
            logger.info("Scheduler already initialized, returning existing instance")
            return _scheduler_instance

        _scheduler_instance = BackgroundScheduler()

        _scheduler_instance.add_job(
            run_daily_report_job,
            trigger='cron',
            hour=18,
            minute=0,
            args=[stock_file_path],
            id='daily_solar_stock_report',
            replace_existing=True,
            misfire_grace_time=300,
            coalesce=True
        )

        _scheduler_instance.add_job(
            run_weekly_report_job,
            trigger='cron',
            day_of_week='mon',
            hour=18,
            minute=0,
            args=[stock_file_path],
            id='weekly_solar_stock_report',
            replace_existing=True,
            misfire_grace_time=600,
            coalesce=True
        )

        _scheduler_instance.add_job(
            lambda: logger.info("Scheduler heartbeat: OK"),
            trigger='interval',
            hours=1,
            id='scheduler_heartbeat',
            replace_existing=True,
            coalesce=True
        )

        logger.info("Scheduler configured: daily 18:00, weekly Mon 18:00, heartbeat hourly")
        return _scheduler_instance

def restart_scheduler(stock_file_path: str) -> bool:
    global _scheduler_instance, _scheduler_started
    try:
        if _scheduler_instance and _scheduler_instance.running:
            _scheduler_instance.shutdown(wait=False)
        _scheduler_instance = None
        _scheduler_started = False
        scheduler = init_scheduler(stock_file_path)
        scheduler.start()
        _scheduler_started = True
        logger.info("Scheduler restarted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to restart scheduler: {e}")
        return False

def is_scheduler_running() -> bool:
    return _scheduler_instance is not None and _scheduler_instance.running
