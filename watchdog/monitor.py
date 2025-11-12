import os, time, json, datetime, subprocess, docker, requests, smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()
client = docker.from_env()

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))
AUTO_REBUILD = os.getenv("AUTO_REBUILD", "true").lower() == "true"
CRITICAL_SERVICES = os.getenv("CRITICAL_SERVICES", "").split(",")
HISTORY_FILE = os.getenv("HISTORY_FILE", "uptime_history.json")
ALERT_METHOD = os.getenv("ALERT_METHOD", "slack")

# Alert configs
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO", EMAIL_USER)

def send_slack_alert(title, msg, color="#FF0000"):
    if not SLACK_WEBHOOK:
        print("[WARN] No Slack webhook set.")
        return
    payload = {
        "attachments": [{
            "fallback": title,
            "color": color,
            "title": title,
            "text": msg,
            "ts": int(time.time())
        }]
    }
    try:
        requests.post(SLACK_WEBHOOK, json=payload)
        print(f"[SLACK] Alert sent: {title}")
    except Exception as e:
        print(f"[ERROR] Slack alert failed: {e}")

def send_email_alert(subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        print("[WARN] Email creds missing.")
        return
    msg = MIMEText(body, "plain")
    msg["Subject"], msg["From"], msg["To"] = subject, EMAIL_USER, EMAIL_TO
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        print(f"[EMAIL] Alert sent to {EMAIL_TO}")
    except Exception as e:
        print(f"[ERROR] Email alert failed: {e}")

def alert(title, msg, color="#FF0000"):
    if ALERT_METHOD == "slack":
        send_slack_alert(title, msg, color)
    elif ALERT_METHOD == "email":
        send_email_alert(title, msg)
    else:
        print(f"[WARN] Unknown alert method {ALERT_METHOD}")

def record(service, status, action):
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service": service,
        "status": status,
        "action": action
    }
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                data = json.load(f)
        except Exception:
            pass
    data.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def rebuild(service):
    if not AUTO_REBUILD:
        record(service, "down", "manual-required")
        return
    try:
        subprocess.run(["docker-compose", "-f", "docker-compose-prod.yml", "up", "-d", "--build", service], check=True)
        record(service, "restarted", "auto-rebuild")
        alert(f"🔁 {service} restarted", "Watchdog auto-rebuilt the service.", "#36A64F")
    except subprocess.CalledProcessError as e:
        alert(f"❌ {service} rebuild failed", str(e))
        record(service, "rebuild_failed", "auto-rebuild")

def monitor():
    print("🐾 Starting Docker Watchdog...")
    while True:
        for svc in CRITICAL_SERVICES:
            svc = svc.strip()
            try:
                c = client.containers.get(svc)
                status = c.status
                print(f"[CHECK] {svc} → {status}")
                if status != "running":
                    alert(f"🚨 {svc} down", f"Service {svc} stopped. Restarting...")
                    rebuild(svc)
                else:
                    record(svc, "healthy", "ok")
            except docker.errors.NotFound:
                alert(f"🚨 Missing container: {svc}", f"Container {svc} not found. Rebuilding...")
                rebuild(svc)
            except Exception as e:
                alert(f"⚠️ Error checking {svc}", str(e))
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
