from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import docker, json, os, asyncio, smtplib, requests
from datetime import datetime
from email.mime.text import MIMEText

app = FastAPI(title="Docker Watchdog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# Config
# ===============================
HISTORY_FILE = os.getenv("HISTORY_FILE", "uptime_history.json")
AUTO_HEAL = os.getenv("AUTO_HEAL", "true").lower() == "true"
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

# Email & Discord alerts (optional)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

client = docker.from_env()


# ===============================
# Utility
# ===============================
def append_history(entry: dict):
    try:
        data = json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []
    except Exception:
        data = []
    data.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ===============================
# Alerts
# ===============================
def send_email_alert(subject, message):
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]):
        print("📧 Skipping email alert (missing config)")
        return
    try:
        msg = MIMEText(message)
        msg["Subject"], msg["From"], msg["To"] = subject, EMAIL_FROM, EMAIL_TO
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"📧 Email sent → {EMAIL_TO}: {subject}")
    except Exception as e:
        print(f"❌ Email send failed: {e}")


def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🚨 {message}"})
        print("🔔 Discord alert sent")
    except Exception as e:
        print(f"❌ Discord alert failed: {e}")


# ===============================
# API Routes
# ===============================
@app.get("/api/health")
def health():
    return {"status": "ok", "auto_heal": AUTO_HEAL}


@app.get("/api/status")
def status():
    containers = client.containers.list(all=True)
    return {
        "containers": [
            {"name": c.name, "status": c.status, "image": c.image.tags[0] if c.image.tags else ""}
            for c in containers
        ]
    }


@app.get("/api/history")
def history(limit: int = 100):
    if not os.path.exists(HISTORY_FILE):
        return {"count": 0, "data": []}
    data = json.load(open(HISTORY_FILE))
    return {"count": len(data), "data": data[-limit:]}


@app.get("/api/container/{name}")
def container_details(name: str):
    """Detailed info for a specific container"""
    try:
        c = client.containers.get(name)
        info = c.attrs
        return {
            "name": c.name,
            "id": c.id,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "",
            "created": info["Created"],
            "ports": info["NetworkSettings"]["Ports"],
            "state": info["State"],
            "mounts": info.get("Mounts", []),
            "network": info["NetworkSettings"]["Networks"],
            "env": info["Config"]["Env"],
        }
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/container/{name}/logs")
def container_logs(name: str, lines: int = 50):
    """Get the latest logs of a container"""
    try:
        c = client.containers.get(name)
        logs = c.logs(tail=lines).decode("utf-8", errors="ignore")
        return {"name": name, "logs": logs.splitlines()}
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/container/{name}/stats")
def container_stats(name: str):
    """Get current CPU and memory usage of a container"""
    try:
        c = client.containers.get(name)
        stats = c.stats(stream=False)
        cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"]
        mem_usage = stats["memory_stats"]["usage"]
        mem_limit = stats["memory_stats"]["limit"]
        mem_percent = round((mem_usage / mem_limit) * 100, 2)
        return {
            "name": c.name,
            "cpu_usage": cpu_usage,
            "mem_usage": round(mem_usage / (1024 * 1024), 2),
            "mem_limit": round(mem_limit / (1024 * 1024), 2),
            "mem_percent": mem_percent,
        }
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}


# ===============================
# Background Task
# ===============================
async def watchdog_loop():
    print(f"🚀 Watchdog started (interval={CHECK_INTERVAL}s, auto_heal={AUTO_HEAL})")
    while True:
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            for c in client.containers.list(all=True):
                entry = {
                    "timestamp": timestamp,
                    "service": c.name,
                    "status": "healthy" if c.status == "running" else "down",
                    "action": "",
                }
                if c.status != "running":
                    alert = f"❌ {c.name} is DOWN (status={c.status})"
                    send_discord_alert(alert)
                    send_email_alert("🚨 Container Down", alert)
                    if AUTO_HEAL:
                        try:
                            c.start()
                            entry["action"] = "auto_restarted"
                            msg = f"✅ Auto-healed {c.name}"
                            send_email_alert("✅ Auto-Healed", msg)
                            send_discord_alert(msg)
                        except Exception as e:
                            entry["action"] = f"restart_failed: {e}"
                append_history(entry)
        except Exception as e:
            print(f"❌ Watchdog error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(watchdog_loop())

@app.post("/api/container/{name}/start")
def start_container(name: str):
    try:
        c = client.containers.get(name)
        c.start()
        return {"status": "started", "name": c.name}
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/container/{name}/stop")
def stop_container(name: str):
    try:
        c = client.containers.get(name)
        c.stop()
        return {"status": "stopped", "name": c.name}
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/container/{name}/restart")
def restart_container(name: str):
    try:
        c = client.containers.get(name)
        c.restart()
        return {"status": "restarted", "name": c.name}
    except docker.errors.NotFound:
        return {"error": f"Container '{name}' not found"}
    except Exception as e:
        return {"error": str(e)}

