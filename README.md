# 🚀 MERN Stack Application + Watchdog Monitoring System (DevOps Production Setup)

This repository contains:

- A **full MERN stack application** (MongoDB, Express/Node, React)
- A **production-ready Dockerized deployment**
- A **Watchdog Monitoring System** built with:
  - FastAPI backend
  - Docker Engine monitoring
  - Auto-healing of containers
  - Real-time Watchdog Dashboard (React + Nginx)
  - Logs, CPU/Memory stats, uptime history, alerts

This README includes **full deployment documentation**, **production architecture**, and **DevOps workflow setup**.

---

# 📁 Project Structure

├── client/ # React frontend
├── server/ # Node.js backend
├── watchdog/ # FastAPI monitoring + auto-heal service
│ ├── api.py # Watchdog API
│ ├── uptime_history.json # Stored health events
│ └── frontend/ # Watchdog React UI (dashboard)
├── docker-compose-prod.yml # Production multi-container stack
├── nginx/ # Additional proxy configs (optional)
├── .env # Global env variables
└── README.md

yaml
Copy code

---

# ⚙️ Tech Stack

### Application
- React (Vite)
- Node.js / Express
- MongoDB
- Axios, JWT Auth

### DevOps
- Docker & Docker Compose
- **nginx-proxy** + **acme-companion** (Auto SSL)
- FastAPI (Watchdog backend)
- React + Nginx (Dashboard)
- GitHub Actions CI/CD
- Monitoring & Alerts (Email / Discord)

---

# 🖥️ Watchdog Monitoring System (New)

You now have a **production-grade monitoring tool**, embedded into the MERN stack deployment.

### 🧩 What Watchdog Does

| Feature | Description |
|--------|-------------|
| **Container Health Monitoring** | Tracks each container (backend, frontend, mongo, nginx, watchdog, dashboard) |
| **Auto-Healing** | If any container goes DOWN → Watchdog automatically restarts it |
| **Live Logs Viewer** | View latest container logs from dashboard |
| **Real-time Stats** | CPU %, Memory Usage, Memory Limits |
| **Uptime History** | Every check is saved to `uptime_history.json` |
| **Alerts** | Email + Discord alerts when container fails |
| **REST API** | `/api/status`, `/api/history`, `/api/container/<name>` |

---

# 🧱 Watchdog API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | API status |
| GET | `/api/status` | All container statuses |
| GET | `/api/history` | Uptime events history |
| GET | `/api/container/<name>` | Container details |
| GET | `/api/container/<name>/logs` | Latest logs |
| GET | `/api/container/<name>/stats` | CPU/Memory stats |

---

# 📊 Watchdog Dashboard (React UI)

### Features:
✔ Table view of all containers  
✔ Click container → view logs, CPU, memory  
✔ Auto-refresh  
✔ Uptime graph  
✔ Recent events feed  
✔ Dark mode UI  
✔ Nginx reverse proxy secured with HTTPS  

Hosted under:

https://dashboard.yourdomain.com

yaml
Copy code

---

# 🛠️ Local Development Setup

```bash
git clone https://github.com/ragav-29/MERN_DEMO_PROJECT.git
cd MERN_DEMO_PROJECT
Backend (server/.env)
env
Copy code
PORT=5000
MONGO_URI=mongodb://mongo:27017/mydatabase
JWT_SECRET=your_jwt_secret
Frontend (client/.env)
env
Copy code
VITE_API_URL=http://localhost:5000/api
Watchdog (watchdog/.env)
env
Copy code
CHECK_INTERVAL=30
AUTO_HEAL=true
EMAIL_FROM=""
EMAIL_TO=""
SMTP_SERVER=""
SMTP_USERNAME=""
SMTP_PASSWORD=""
DISCORD_WEBHOOK_URL=""
Start locally:
bash
Copy code
docker-compose up --build
🛰️ Production Deployment (Docker Compose)
Start production stack:
bash
Copy code
docker-compose -f docker-compose-prod.yml up -d --build
Services deployed:
Service	Domain	Port
Frontend	https://ragav.space	via nginx
Backend	https://api.ragav.space	via nginx
Watchdog API	https://watchdog.ragav.space	8001
Dashboard UI	https://dashboard.ragav.space	via nginx
MongoDB	internal only	27017

🌐 Auto SSL Reverse Proxy (nginx-proxy + acme-companion)
Certificates auto-renew.
Fully automated with environment variables:

yml
Copy code
VIRTUAL_HOST=ragav.space
LETSENCRYPT_HOST=ragav.space
LETSENCRYPT_EMAIL=you@example.com
🧪 Watchdog Testing
Check API:
bash
Copy code
curl -I https://watchdog.yourdomain.com/api/status
Check Dashboard:
Open:

arduino
Copy code
https://dashboard.yourdomain.com
📚 Useful Docker Commands
bash
Copy code
docker ps
docker logs -f watchdog
docker logs -f backend
docker exec -it mongo sh
docker stats
docker-compose down
🧩 Architecture Diagram
bash
Copy code
          ┌─────────────────────────────┐
          │       User Browser          │
          └──────────────┬──────────────┘
                         https
                  ┌──────────────┐
                  │ nginx-proxy  │
                  └─────┬────────┘
        ┌────────────────────────────────────┬───────────────────────────┐
        │                                    │                           │
 https://ragav.space                https://api.ragav.space    https://dashboard.ragav.space
        ▼                                    ▼                           ▼
┌─────────────┐                     ┌────────────────┐          ┌──────────────────────┐
│  Frontend   │                     │  Backend API   │          │ Watchdog Dashboard   │
└─────────────┘                     └────────────────┘          └──────────┬───────────┘
                                                                             │ API Call
                                                                     https://watchdog.domain.com
                                                                             ▼
                                                                    ┌───────────────────┐
                                                                    │   Watchdog API    │
                                                                    │ Auto-heal + Logs  │
                                                                    └─────────┬─────────┘
                                                                              │
                                                                  ┌──────────────────────┐
                                                                  │ Docker Engine Socket │
                                                                  └──────────────────────┘
🛡️ CI/CD (GitHub Actions)
Automatically:

✔ Builds frontend & backend
✔ Runs tests
✔ Builds Docker images
✔ Pushes images
✔ SSH deploys or triggers webhook

🤝 Contributing
Fork

git checkout -b feature/devops

Commit

PR

📞 Contact
Email: ragav29596@gmail.com
GitHub: https://github.com/ragav-29
