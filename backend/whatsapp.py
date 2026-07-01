import json
import time
import datetime
import logging
import urllib.request
import urllib.error
import ssl

logger = logging.getLogger("solar_app.whatsapp")

API_BASE = "https://graph.facebook.com/v21.0"
MAX_RETRIES = 3
RETRY_DELAY = 5
BACKOFF_MULTIPLIER = 2
REQUEST_TIMEOUT = 15

def _build_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

def _do_request(url: str, data: dict, headers: dict) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "response": response_data}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"WhatsApp HTTP {e.code}: {error_body}")
        try:
            err_detail = json.loads(error_body)
            msg = err_detail.get("error", {}).get("message", error_body)
        except (json.JSONDecodeError, AttributeError):
            msg = error_body
        return {"success": False, "error": f"HTTP {e.code}: {msg}", "http_code": e.code}
    except urllib.error.URLError as e:
        logger.error(f"WhatsApp URL error: {e.reason}")
        return {"success": False, "error": f"Network error: {e.reason}"}
    except Exception as e:
        logger.error(f"WhatsApp request error: {e}")
        return {"success": False, "error": str(e)}

def send_text_message(phone_number_id: str, access_token: str, recipient: str, text: str) -> dict:
    url = f"{API_BASE}/{phone_number_id}/messages"
    headers = _build_headers(access_token)
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    }
    logger.info(f"Sending WhatsApp message to {recipient[:4]}...{recipient[-3:]}")
    return _do_request(url, payload, headers)

def send_text_message_with_retry(phone_number_id: str, access_token: str, recipient: str, text: str) -> dict:
    last_error = None
    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"WhatsApp attempt {attempt}/{MAX_RETRIES}")
        result = send_text_message(phone_number_id, access_token, recipient, text)
        if result.get("success"):
            logger.info(f"WhatsApp message sent successfully (attempt {attempt})")
            return result
        last_error = result.get("error", "Unknown error")
        http_code = result.get("http_code")
        if http_code == 401:
            logger.error("WhatsApp: Invalid token (401). Not retrying.")
            return result
        if attempt < MAX_RETRIES:
            logger.warning(f"WhatsApp attempt {attempt} failed: {last_error}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= BACKOFF_MULTIPLIER
    logger.error(f"All {MAX_RETRIES} WhatsApp attempts failed. Last error: {last_error}")
    return {"success": False, "error": last_error or "Failed after retries"}

def validate_connection(phone_number_id: str, access_token: str) -> dict:
    url = f"{API_BASE}/{phone_number_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            logger.info("WhatsApp connection validated successfully")
            name = data.get("display_phone_number") or data.get("verified_name") or "Connected"
            return {"success": True, "message": f"Connected: {name}"}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        err_msg = error_body
        try:
            err_detail = json.loads(error_body)
            err_msg = err_detail.get("error", {}).get("message", error_body)
        except (json.JSONDecodeError, AttributeError):
            pass
        logger.error(f"WhatsApp validation failed: {e.code} - {err_msg}")
        if e.code == 401:
            return {"success": False, "error": "Invalid or expired access token"}
        return {"success": False, "error": f"Validation failed: {err_msg}"}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_test_message(phone_number_id: str, access_token: str, recipient: str) -> dict:
    today = datetime.date.today().strftime("%d/%m/%Y")
    text = (
        "📦 Solar Stock Management\n\n"
        "WhatsApp Connection Successful\n\n"
        f"Date: {today}\n\n"
        "This is a test message from your\n"
        "Stock Management System.\n\n"
        "✅ All systems operational."
    )
    return send_text_message_with_retry(phone_number_id, access_token, recipient, text)

def format_daily_whatsapp_report(products: list, transactions: list) -> str:
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    today_iso = datetime.date.today().isoformat()
    stock_in_lines = []
    stock_out_lines = []
    for tx in transactions:
        tx_date = tx.get("date", "")
        if tx_date == today_iso:
            p_name = tx.get("product_name", "Unknown")
            qty = tx.get("quantity", 0)
            if tx.get("type") == "IN":
                stock_in_lines.append(f"• {p_name} : +{qty}")
            elif tx.get("type") == "OUT":
                stock_out_lines.append(f"• {p_name} : -{qty}")
    category_stock = {}
    low_stock_items = []
    for p in products:
        cat = p.get("category", "Uncategorized")
        name = p.get("name", "")
        qty = p.get("quantity", 0)
        min_stock = p.get("minimum_stock", 0)
        if cat not in category_stock:
            category_stock[cat] = []
        category_stock[cat].append(f"  {name} : {qty}")
        if qty < min_stock:
            low_stock_items.append(f"  {name}")
    stock_in_section = "\n".join(stock_in_lines) if stock_in_lines else "  None"
    stock_out_section = "\n".join(stock_out_lines) if stock_out_lines else "  None"
    cat_sections = []
    for cat, items in category_stock.items():
        cat_sections.append(f"\n{cat}\n" + "\n".join(items))
    current_stock_section = "".join(cat_sections) if cat_sections else "\n  No products in stock"
    low_stock_section = "\n".join(low_stock_items) if low_stock_items else "  None"
    total_products = len(products)
    available_stock = sum(p.get("quantity", 0) for p in products)
    text = (
        f"📦 Solar Stock Management\n"
        f"Daily Inventory Report\n\n"
        f"Date: {today_str}\n\n"
        f"📊 Overview\n"
        f"  Products: {total_products}\n"
        f"  Total Stock: {available_stock}\n\n"
        f"📈 Stock In\n{stock_in_section}\n\n"
        f"📉 Stock Out\n{stock_out_section}\n\n"
        f"📋 Current Stock\n{current_stock_section}\n\n"
        f"⚠️ Low Stock\n{low_stock_section}\n\n"
        f"Generated Automatically"
    )
    return text

def send_daily_whatsapp_report(config: dict, products: list, transactions: list) -> dict:
    phone_number_id = config.get("whatsapp_phone_number_id", "")
    whatsapp_token = config.get("whatsapp_token", "")
    recipient = config.get("whatsapp_recipient", "")
    if not phone_number_id or not whatsapp_token or not recipient:
        return {"success": False, "error": "WhatsApp not configured"}
    text = format_daily_whatsapp_report(products, transactions)
    return send_text_message_with_retry(phone_number_id, whatsapp_token, recipient, text)
