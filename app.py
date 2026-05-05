#!/usr/bin/env python3
"""
APP.PY - Web Server cho Railway
================================
- Hien thi dashboard tai URL cong khai
- Tu dong fetch du lieu theo lich
- Gui email tin hieu kep
- Co nut Load thu cong tren web
"""

import os, json, threading, smtplib, schedule, time
from datetime import datetime, timezone
from flask import Flask, jsonify, send_from_directory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import logic fetch tu file chinh
from ma_dashboard_fetcher import fetch_all, build_html
from symbols import SYMBOLS

app = Flask(__name__, static_folder="static")

# ============================================================
# CAU HINH - lay tu Environment Variables tren Railway
# ============================================================
EMAIL_TO       = os.environ.get("EMAIL_TO",       "ch2000vn@gmail.com")
EMAIL_FROM     = os.environ.get("EMAIL_FROM",     "ch2000vn@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
SCHEDULE_HOURS = [3, 7, 11, 15, 19, 23]
PORT           = int(os.environ.get("PORT", 8080))

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dashboard_data.json")
HTML_FILE = os.path.join(BASE_DIR, "dashboard.html")

# Lock tranh chay dong thoi
fetch_lock    = threading.Lock()
is_fetching   = False
last_updated  = None

# ============================================================
# GUI EMAIL
# ============================================================
def send_email(strong_buy, strong_sell, all_data, updated_at):
    if not EMAIL_PASSWORD:
        print("  [EMAIL] Chua cau hinh EMAIL_PASSWORD - bo qua")
        return

    total = len(strong_buy) + len(strong_sell)
    subject = f"[Tin hieu kep] {total} ma | {updated_at}" if total > 0 else f"[Bao cao] Khong co tin hieu kep | {updated_at}"

    def make_rows(rows, color):
        html = ""
        for r in rows:
            d1   = "Tren MA50" if r.get("d1_above50") else "Duoi MA50"
            h4   = "Tren MA50" if r.get("h4_above50") else "Duoi MA50"
            macd_map = {"crossed_up":"Da cat len","crossed_down":"Da cat xuong",
                        "about_up":"Sap cat len","about_down":"Sap cat xuong",
                        "normal":"Binh thuong","nodata":"No data"}
            macd = macd_map.get(r.get("macd_status",""), "")
            hist = r.get("macd_hist") or 0
            hist_str = f"+{hist}" if hist > 0 else str(hist)
            price = f"{r['d1_price']:,.5f}" if r.get("d1_price") else "—"
            bg = "#F0FAF5" if color=="#1D9E75" else "#FDF0EE"
            html += f"""<tr style="background:{bg};">
              <td style="padding:8px 12px;font-weight:700;color:{color};">{r['sym']}</td>
              <td style="padding:8px 12px;color:#666;">{r['cat']}</td>
              <td style="padding:8px 12px;">{d1}</td>
              <td style="padding:8px 12px;">{h4}</td>
              <td style="padding:8px 12px;font-weight:600;color:{color};">{macd}</td>
              <td style="padding:8px 12px;">{hist_str}</td>
              <td style="padding:8px 12px;">{price}</td>
            </tr>"""
        return html

    buy_rows  = make_rows(strong_buy,  "#1D9E75")
    sell_rows = make_rows(strong_sell, "#D85A30")

    def section(rows_html, color, label, count):
        if not rows_html: return ""
        return f"""
        <h3 style="color:{color};margin:20px 0 8px;">{label} ({count} ma)</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead><tr style="background:#f0f0f0;">
            <th style="padding:8px 12px;text-align:left;">Ma</th>
            <th style="padding:8px 12px;text-align:left;">Nhom</th>
            <th style="padding:8px 12px;text-align:left;">D1/MA50</th>
            <th style="padding:8px 12px;text-align:left;">H4/MA50</th>
            <th style="padding:8px 12px;text-align:left;">MACD H4</th>
            <th style="padding:8px 12px;text-align:left;">Histogram</th>
            <th style="padding:8px 12px;text-align:left;">Gia</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>"""

    no_signal = "" if total > 0 else """
        <div style="background:#FFF8E1;border-left:4px solid #F59E0B;padding:12px 16px;border-radius:4px;margin:16px 0;">
          <strong>Khong co tin hieu kep</strong> trong phien nay.
        </div>"""

    html_body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#1a1a18;">
      <div style="background:#1a1a18;color:#fff;padding:16px 20px;border-radius:8px;margin-bottom:20px;">
        <h2 style="margin:0;">Phan tich Xu Huong &amp; Tin Hieu</h2>
        <p style="margin:4px 0 0;color:#aaa;font-size:12px;">Cap nhat: {updated_at}</p>
      </div>
      {no_signal}
      {section(buy_rows,  "#1D9E75", "TIN HIEU KEP MUA", len(strong_buy))}
      {section(sell_rows, "#D85A30", "TIN HIEU KEP BAN", len(strong_sell))}
      <div style="margin-top:24px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#aaa;">
        Du lieu tu yFinance - chi mang tinh tham khao, khong phai khuyen nghi dau tu.
      </div>
    </body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = EMAIL_TO
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Thu port 587 (TLS) truoc, neu loi thi thu 465 (SSL)
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
                smtp.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        except Exception:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
                smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
                smtp.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        print(f"  [EMAIL] Gui thanh cong -> {EMAIL_TO}")
    except smtplib.SMTPAuthenticationError:
        print("  [EMAIL] Loi xac thuc - kiem tra EMAIL_PASSWORD")
    except Exception as e:
        print(f"  [EMAIL] Loi: {e}")

# ============================================================
# FETCH DU LIEU
# ============================================================
def run_fetch(send_mail=True):
    global is_fetching, last_updated
    if is_fetching:
        print("  [FETCH] Dang chay, bo qua...")
        return

    with fetch_lock:
        is_fetching = True
        now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        print(f"\n[{now}] Bat dau fetch du lieu...")
        try:
            data = fetch_all()

            # Luu HTML
            html = build_html(data)
            with open(HTML_FILE, "w", encoding="utf-8") as f:
                f.write(html)

            # Luu JSON
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            # Loc tin hieu kep
            MACD_UP = ["crossed_up","about_up"]
            MACD_DN = ["crossed_down","about_down"]
            strong_buy  = [r for r in data if r.get("signal")=="bull" and r.get("macd_status") in MACD_UP]
            strong_sell = [r for r in data if r.get("signal")=="bear" and r.get("macd_status") in MACD_DN]

            print(f"  [OK] Fetch xong! MUA={len(strong_buy)} BAN={len(strong_sell)}")

            if send_mail:
                updated_at = datetime.now().strftime("%H:%M %d/%m/%Y")
                send_email(strong_buy, strong_sell, data, updated_at)

        except Exception as e:
            print(f"  [LOI] Fetch that bai: {e}")
        finally:
            is_fetching = False

# ============================================================
# ROUTES
# ============================================================
@app.route("/")
def index():
    """Trang chu - hien thi dashboard."""
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, encoding="utf-8") as f:
            return f.read()
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
      <h2>Dang tai du lieu lan dau...</h2>
      <p>Vui long cho 1-2 phut roi refresh trang.</p>
      <p style="color:#888;font-size:12px;">Du lieu dang duoc fetch tu yFinance</p>
      <script>setTimeout(()=>location.reload(), 30000)</script>
    </body></html>"""

@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    """API endpoint cho nut Load tren dashboard."""
    if is_fetching:
        return jsonify({"status": "busy", "message": "Dang fetch, vui long cho..."})
    t = threading.Thread(target=run_fetch, kwargs={"send_mail": False})
    t.daemon = True
    t.start()
    return jsonify({"status": "ok", "message": "Bat dau fetch du lieu moi"})

@app.route("/api/status")
def api_status():
    """Kiem tra trang thai."""
    return jsonify({
        "status":       "ok",
        "is_fetching":  is_fetching,
        "last_updated": last_updated,
        "next_run":     str(schedule.next_run()),
    })

@app.route("/health")
def health():
    return "OK", 200

@app.route("/test-email")
def test_email():
    """Test gui email - mo URL nay tren browser de kiem tra."""
    try:
        updated_at = datetime.now().strftime("%H:%M %d/%m/%Y")
        fake_buy  = [{"sym":"EURUSD","cat":"forex","d1_above50":True,
                      "h4_above50":True,"macd_status":"about_up",
                      "macd_hist":-0.00012,"d1_price":1.17233}]
        fake_sell = [{"sym":"USDCAD","cat":"forex","d1_above50":False,
                      "h4_above50":False,"macd_status":"about_down",
                      "macd_hist":0.00008,"d1_price":1.35880}]
        send_email(fake_buy, fake_sell, fake_buy + fake_sell, updated_at)
        return f"""
        <html><body style="font-family:sans-serif;padding:40px;max-width:500px;margin:0 auto;">
          <h2 style="color:#1D9E75;">Email da duoc gui!</h2>
          <p>Kiem tra hop thu: <strong>{EMAIL_TO}</strong></p>
          <p style="color:#888;font-size:13px;">
            Neu khong thay email sau 1 phut:<br>
            - Kiem tra thu muc Spam<br>
            - Kiem tra lai EMAIL_PASSWORD (phai dung App Password)<br>
            - Dam bao 2-Step Verification da bat tren Gmail
          </p>
          <a href="/" style="color:#534AB7;">← Quay lai dashboard</a>
        </body></html>"""
    except Exception as e:
        return f"""
        <html><body style="font-family:sans-serif;padding:40px;">
          <h2 style="color:#D85A30;">Loi gui email!</h2>
          <p><code>{str(e)}</code></p>
          <p>Kiem tra lai EMAIL_PASSWORD trong Variables.</p>
        </body></html>""", 500

# ============================================================
# SCHEDULER THREAD
# ============================================================
def run_scheduler():
    for hour in SCHEDULE_HOURS:
        schedule.every().day.at(f"{hour:02d}:05").do(run_fetch)
        print(f"  Lich: {hour:02d}:05 hang ngay")

    print(f"  Next run: {schedule.next_run()}")
    while True:
        schedule.run_pending()
        time.sleep(30)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("  Phan tich Xu Huong & Tin Hieu - Railway")
    print("=" * 55)
    print(f"  Port: {PORT}")
    print(f"  Email: {EMAIL_TO}")
    print(f"  Lich: {', '.join(str(h)+'h' for h in SCHEDULE_HOURS)}")
    print("=" * 55)

    # Khoi dong scheduler trong thread rieng
    sched_thread = threading.Thread(target=run_scheduler, daemon=True)
    sched_thread.start()

    # Fetch ngay lan dau khi khoi dong
    fetch_thread = threading.Thread(target=run_fetch, kwargs={"send_mail": False}, daemon=True)
    fetch_thread.start()

    # Khoi dong web server
    app.run(host="0.0.0.0", port=PORT, debug=False)
