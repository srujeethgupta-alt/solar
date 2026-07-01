import datetime
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("solar_app.emailer")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
BACKOFF_MULTIPLIER = 2

def test_smtp_connection(config: dict) -> dict:
    smtp_server = config.get("email_smtp_server", "")
    smtp_port = config.get("email_smtp_port", 587)
    sender = config.get("email_sender", "")
    password = config.get("email_password", "")
    if not smtp_server or not sender or not password:
        return {"success": False, "error": "Email settings not configured"}
    try:
        logger.info(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.quit()
        return {"success": True, "message": "SMTP connection successful"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "SMTP authentication failed. Use an App Password for Gmail."}
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {str(e)}"}

def send_email_report(config: dict, report_text: str, html_body: str = None, subject: str = None) -> dict:
    smtp_server = config.get("email_smtp_server", "")
    smtp_port = config.get("email_smtp_port", 587)
    sender = config.get("email_sender", "")
    password = config.get("email_password", "")
    recipient_raw = config.get("email_recipient", "")

    if not smtp_server or not sender or not password or not recipient_raw:
        logger.error("Email settings not fully configured.")
        return {"success": False, "error": "Email credentials not configured in settings."}

    recipients = [r.strip() for r in recipient_raw.replace(";", ",").split(",") if r.strip()]

    if not recipients:
        return {"success": False, "error": "No valid recipient email addresses configured."}

    last_error = None
    delay = RETRY_DELAY_SECONDS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            if subject:
                msg["Subject"] = subject
            else:
                msg["Subject"] = f"Solar Store Daily Report - {datetime.date.today().strftime('%d/%m/%Y')}"
            msg.attach(MIMEText(report_text, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            logger.info(f"Email attempt {attempt}/{MAX_RETRIES}: connecting to {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return {"success": True, "message": f"Email sent to {', '.join(recipients)}"}
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed.")
            return {"success": False, "error": "SMTP authentication failed. Use an App Password for Gmail."}
        except smtplib.SMTPException as e:
            last_error = f"SMTP error: {str(e)}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {last_error}")
        if attempt < MAX_RETRIES:
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)
            delay *= BACKOFF_MULTIPLIER

    logger.error(f"All {MAX_RETRIES} email attempts failed. Last error: {last_error}")
    return {"success": False, "error": last_error or "Failed to send email after multiple attempts."}

def format_daily_report(products: list, transactions: list) -> str:
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    today_iso = datetime.date.today().isoformat()
    stock_in_lines = []
    stock_out_lines = []
    for tx in transactions:
        tx_date = tx.get("date", "")
        if tx_date == today_iso:
            p_name = tx.get("product_name", "Unknown Product")
            qty = tx.get("quantity", 0)
            if tx.get("type") == "IN":
                stock_in_lines.append(f"Stock In - {p_name}: +{qty}")
            elif tx.get("type") == "OUT":
                stock_out_lines.append(f"Stock Out - {p_name}: -{qty}")
    category_stock = {}
    low_stock_lines = []
    for p in products:
        cat = p.get("category", "Uncategorized")
        name = p.get("name", "")
        model = p.get("model_capacity", "")
        qty = p.get("quantity", 0)
        min_stock = p.get("minimum_stock", 0)
        display_name = f"{name} ({model})" if model else name
        if cat not in category_stock:
            category_stock[cat] = []
        category_stock[cat].append(f"  - {display_name}: {qty}")
        if qty < min_stock:
            low_stock_lines.append(f"Low Stock - {display_name} (Qty: {qty} < Min: {min_stock})")
    current_stock_lines = []
    for cat, items in category_stock.items():
        current_stock_lines.append(f"[{cat}]")
        current_stock_lines.extend(items)
    stock_in_section = "\n".join(stock_in_lines) if stock_in_lines else "None"
    stock_out_section = "\n".join(stock_out_lines) if stock_out_lines else "None"
    current_stock_section = "\n".join(current_stock_lines) if current_stock_lines else "No products in stock"
    low_stock_section = "\n".join(low_stock_lines) if low_stock_lines else "All stock levels healthy"
    report = (
        f"SOLAR STORE DAILY REPORT\n"
        f"Date: {today_str}\n\n"
        f"STOCK IN (Today)\n{stock_in_section}\n\n"
        f"STOCK OUT (Today)\n{stock_out_section}\n\n"
        f"CURRENT STOCK BY CATEGORY\n{current_stock_section}\n\n"
        f"LOW STOCK ALERTS\n{low_stock_section}\n\n"
        f"Thank you."
    )
    return report

def format_html_report(products: list, transactions: list) -> str:
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    today_iso = datetime.date.today().isoformat()
    rows_html = ""
    for tx in transactions:
        tx_date = tx.get("date", "")
        if tx_date == today_iso:
            p_name = tx.get("product_name", "Unknown Product")
            qty = tx.get("quantity", 0)
            ttype = tx.get("type", "")
            badge = '<span style="background:#22C55E;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">IN</span>' if ttype == "IN" else '<span style="background:#EF4444;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">OUT</span>'
            sign = f"+{qty}" if ttype == "IN" else f"-{qty}"
            rows_html += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{badge}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{p_name}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;font-weight:bold;'>{sign}</td></tr>"
    cat_rows = ""
    category_stock = {}
    low_stock_rows = ""
    for p in products:
        cat = p.get("category", "Uncategorized")
        name = p.get("name", "")
        qty = p.get("quantity", 0)
        min_stock = p.get("minimum_stock", 0)
        if cat not in category_stock:
            category_stock[cat] = []
        category_stock[cat].append(f"<li>{name}: <strong>{qty}</strong></li>")
        if qty < min_stock:
            bar_color = "#EF4444" if qty == 0 else "#F59E0B"
            bar_width = max(5, int((qty / max(min_stock, 1)) * 100))
            low_stock_rows += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{name}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{qty} / {min_stock}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'><div style='background:#e2e8f0;border-radius:4px;height:8px;width:100px;'><div style='background:{bar_color};width:{bar_width}%;height:8px;border-radius:4px;'></div></div></td></tr>"
    for cat, items in category_stock.items():
        cat_rows += f"<h4 style='color:#FFC107;margin:10px 0 4px;'>{cat}</h4><ul style='margin:0 0 12px;padding-left:20px;color:#475569;'>{''.join(items)}</ul>"
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>body{{font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:20px;}}.card{{background:white;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);}}.header{{background:linear-gradient(135deg,#FFC107,#E5A100);border-radius:12px;padding:24px;margin-bottom:16px;color:#000;}}.header h1{{margin:0;font-size:22px;}}.header p{{margin:4px 0 0;opacity:0.8;font-size:14px;}}</style></head>
<body>
<div class="header"><h1>Solar Store Daily Report</h1><p>{today_str}</p></div>
<div class="card"><h3 style="margin:0 0 12px;">Today's Transactions</h3><table style="width:100%;border-collapse:collapse;">{rows_html or '<p style="color:#94a3b8;">No transactions today.</p>'}</table></div>
<div class="card"><h3 style="margin:0 0 12px;">Current Stock by Category</h3>{cat_rows}</div>
<div class="card"><h3 style="margin:0 0 12px;">Low Stock Alerts</h3>{"<table style='width:100%;border-collapse:collapse;'><tr><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Product</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Stock</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Level</th></tr>" + low_stock_rows + "</table>" if low_stock_rows else '<p style="color:#22C55E;">All stock levels healthy</p>'}</div>
<p style="color:#94a3b8;font-size:12px;text-align:center;">New High Energy Solar - Automated Report</p>
</body>
</html>"""
    return html

def format_weekly_report(products: list, transactions: list) -> tuple:
    today = datetime.date.today()
    last_monday = today - datetime.timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + datetime.timedelta(days=6)
    start_str = last_monday.strftime("%d/%m/%Y")
    end_str = last_sunday.strftime("%d/%m/%Y")
    period = f"{start_str} - {end_str}"
    stock_in_lines = []
    stock_out_lines = []
    daily_breakdown = {}
    for tx in transactions:
        tx_date = tx.get("date", "")
        try:
            d = datetime.datetime.strptime(tx_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if last_monday <= d <= last_sunday:
            p_name = tx.get("product_name", "Unknown Product")
            qty = tx.get("quantity", 0)
            if tx.get("type") == "IN":
                stock_in_lines.append(f"  {tx_date} - {p_name}: +{qty}")
            elif tx.get("type") == "OUT":
                stock_out_lines.append(f"  {tx_date} - {p_name}: -{qty}")
            daily_breakdown[tx_date] = daily_breakdown.get(tx_date, {"in": 0, "out": 0})
            if tx.get("type") == "IN":
                daily_breakdown[tx_date]["in"] += qty
            else:
                daily_breakdown[tx_date]["out"] += qty
    daily_lines = []
    for d in sorted(daily_breakdown.keys()):
        dd = daily_breakdown[d]
        daily_lines.append(f"  {d}: +{dd['in']} IN / -{dd['out']} OUT")
    in_total = sum(v["in"] for v in daily_breakdown.values())
    out_total = sum(v["out"] for v in daily_breakdown.values())
    category_stock = {}
    low_stock_lines = []
    for p in products:
        cat = p.get("category", "Uncategorized")
        name = p.get("name", "")
        model = p.get("model_capacity", "")
        qty = p.get("quantity", 0)
        min_stock = p.get("minimum_stock", 0)
        display_name = f"{name} ({model})" if model else name
        if cat not in category_stock:
            category_stock[cat] = []
        category_stock[cat].append(f"  - {display_name}: {qty}")
        if qty < min_stock:
            low_stock_lines.append(f"Low Stock - {display_name} (Qty: {qty} < Min: {min_stock})")
    current_stock_lines = []
    for cat, items in category_stock.items():
        current_stock_lines.append(f"[{cat}]")
        current_stock_lines.extend(items)
    total_products = len(products)
    available_stock = sum(p.get("quantity", 0) for p in products)
    report = (
        f"SOLAR STORE WEEKLY REPORT\n"
        f"Period: {period}\n\n"
        f"OVERVIEW\n"
        f"  Total Products: {total_products}\n"
        f"  Available Stock: {available_stock}\n"
        f"  Total Inflow: {in_total}\n"
        f"  Total Outflow: {out_total}\n\n"
        f"DAILY BREAKDOWN\n"
        + ("\n".join(daily_lines) if daily_lines else "  No transactions this week.") +
        f"\n\nSTOCK IN (Week)\n" + ("\n".join(stock_in_lines) if stock_in_lines else "  None") +
        f"\n\nSTOCK OUT (Week)\n" + ("\n".join(stock_out_lines) if stock_out_lines else "  None") +
        f"\n\nCURRENT STOCK BY CATEGORY\n" + "\n".join(current_stock_lines) +
        f"\n\nLOW STOCK ALERTS\n" + ("\n".join(low_stock_lines) if low_stock_lines else "  All stock levels healthy") +
        f"\n\nThank you."
    )
    return report, period

def format_weekly_html_report(products: list, transactions: list) -> str:
    today = datetime.date.today()
    last_monday = today - datetime.timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + datetime.timedelta(days=6)
    period = f"{last_monday.strftime('%d/%m/%Y')} - {last_sunday.strftime('%d/%m/%Y')}"
    tx_rows = ""
    daily_rows = ""
    daily_map = {}
    for tx in transactions:
        tx_date = tx.get("date", "")
        try:
            d = datetime.datetime.strptime(tx_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if last_monday <= d <= last_sunday:
            p_name = tx.get("product_name", "Unknown Product")
            qty = tx.get("quantity", 0)
            ttype = tx.get("type", "")
            badge = '<span style="background:#22C55E;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">IN</span>' if ttype == "IN" else '<span style="background:#EF4444;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">OUT</span>'
            sign = f"+{qty}" if ttype == "IN" else f"-{qty}"
            tx_rows += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{tx_date}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{badge}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{p_name}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;font-weight:bold;'>{sign}</td></tr>"
            daily_map[tx_date] = daily_map.get(tx_date, {"in": 0, "out": 0})
            if ttype == "IN":
                daily_map[tx_date]["in"] += qty
            else:
                daily_map[tx_date]["out"] += qty
    for d in sorted(daily_map.keys()):
        dd = daily_map[d]
        daily_rows += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{d}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;color:#22C55E;'>+{dd['in']}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;color:#EF4444;'>-{dd['out']}</td></tr>"
    in_total = sum(v["in"] for v in daily_map.values())
    out_total = sum(v["out"] for v in daily_map.values())
    total_products = len(products)
    available_stock = sum(p.get("quantity", 0) for p in products)
    category_stock = {}
    low_stock_rows_s = ""
    for p in products:
        cat = p.get("category", "Uncategorized")
        name = p.get("name", "")
        qty = p.get("quantity", 0)
        min_stock = p.get("minimum_stock", 0)
        if cat not in category_stock:
            category_stock[cat] = []
        category_stock[cat].append(f"<li>{name}: <strong>{qty}</strong></li>")
        if qty < min_stock:
            bar_color = "#EF4444" if qty == 0 else "#F59E0B"
            bar_width = max(5, int((qty / max(min_stock, 1)) * 100))
            low_stock_rows_s += f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{name}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'>{qty} / {min_stock}</td><td style='padding:6px 10px;border-bottom:1px solid #eee;'><div style='background:#e2e8f0;border-radius:4px;height:8px;width:100px;'><div style='background:{bar_color};width:{bar_width}%;height:8px;border-radius:4px;'></div></div></td></tr>"
    cat_rows_s = ""
    for cat, items in category_stock.items():
        cat_rows_s += f"<h4 style='color:#FFC107;margin:10px 0 4px;'>{cat}</h4><ul style='margin:0 0 12px;padding-left:20px;color:#475569;'>{''.join(items)}</ul>"
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>body{{font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:20px;}}.card{{background:white;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);}}.header{{background:linear-gradient(135deg,#FFC107,#E5A100);border-radius:12px;padding:24px;margin-bottom:16px;color:#000;}}.header h1{{margin:0;font-size:22px;}}.header p{{margin:4px 0 0;opacity:0.8;font-size:14px;}}</style></head>
<body>
<div class="header"><h1>Solar Store Weekly Report</h1><p>{period}</p></div>
<div class="card">
<h3 style='margin:0 0 12px;'>Summary</h3>
<table style='width:100%;border-collapse:collapse;'>
<tr><td style='padding:8px;font-weight:bold;'>Total Products</td><td style='padding:8px;'>{total_products}</td></tr>
<tr><td style='padding:8px;font-weight:bold;'>Available Stock</td><td style='padding:8px;'>{available_stock}</td></tr>
<tr><td style='padding:8px;font-weight:bold;color:#22C55E;'>Total Inflow</td><td style='padding:8px;'>+{in_total}</td></tr>
<tr><td style='padding:8px;font-weight:bold;color:#EF4444;'>Total Outflow</td><td style='padding:8px;'>-{out_total}</td></tr>
</table>
</div>
<div class="card"><h3 style='margin:0 0 12px;'>Daily Breakdown</h3><table style='width:100%;border-collapse:collapse;'><tr><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Date</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>In</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Out</th></tr>{daily_rows or '<tr><td colspan="3" style="padding:6px 10px;color:#94a3b8;">No transactions this week.</td></tr>'}</table></div>
<div class="card"><h3 style='margin:0 0 12px;'>All Transactions (Week)</h3><table style='width:100%;border-collapse:collapse;'><tr><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Date</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Type</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Product</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Qty</th></tr>{tx_rows or '<tr><td colspan="4" style="padding:6px 10px;color:#94a3b8;">No transactions this week.</td></tr>'}</table></div>
<div class="card"><h3 style='margin:0 0 12px;'>Current Stock by Category</h3>{cat_rows_s}</div>
<div class="card"><h3 style='margin:0 0 12px;'>Low Stock Alerts</h3>{"<table style='width:100%;border-collapse:collapse;'><tr><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Product</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Stock</th><th style='text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;'>Level</th></tr>" + low_stock_rows_s + "</table>" if low_stock_rows_s else '<p style="color:#22C55E;">All stock levels healthy</p>'}</div>
<p style="color:#94a3b8;font-size:12px;text-align:center;">New High Energy Solar - Weekly Automated Report</p>
</body>
</html>"""
    return html
