# MONGO DB BACKUP SCRIPT

#!/bin/bash
# Config
BACKUP_DIR="/var/backups/mongo"
TIMESTAMP=$(date +"%F_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/mongo-$TIMESTAMP.archive.gz"

# Azure Storage Config
STORAGE_ACCOUNT="yourstorageaccount"
CONTAINER_NAME="mongo-backups"
SAS_TOKEN="?sv=2025-01-01&ss=b&srt=co&sp=rwl&se=2025-12-31T23:59:59Z&st=2025-01-01T00:00:00Z&spr=https&sig=XXXX"

mkdir -p "$BACKUP_DIR"

# Run mongodump inside the mongo container
docker exec mongo mongodump --archive --gzip > "$BACKUP_FILE"

# Upload to Azure Blob Storage
azcopy copy "$BACKUP_FILE" "https://$STORAGE_ACCOUNT.blob.core.windows.net/$CONTAINER_NAME/mongo-$TIMESTAMP.archive.gz$SAS_TOKEN"

# Keep only last 7 days of local backups
find "$BACKUP_DIR" -type f -mtime +7 -delete
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#PYTHON MYSQL BACKUP SCRIPT

import subprocess
import datetime
from azure.storage.blob import BlobServiceClient

# Config
container_name = "mysql-container"
db_user = "root"
db_pass = "yourpassword"
db_name = "yourdb"
backup_dir = "/var/backups/mysql"
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
backup_file = f"{backup_dir}/mysql-{db_name}-{timestamp}.sql.gz"

# Azure config
connection_string = "DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
azure_container = "mysql-backups"

# Dump DB
with open(backup_file, "wb") as f:
    subprocess.run([
        "docker", "exec", container_name, "mysqldump",
        f"-u{db_user}", f"-p{db_pass}", db_name
    ], stdout=subprocess.PIPE)
    subprocess.run(["gzip"], stdin=subprocess.PIPE, stdout=f)

# Upload to Azure
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
blob_client = blob_service_client.get_blob_client(container=azure_container, blob=f"mysql-{db_name}-{timestamp}.sql.gz")

with open(backup_file, "rb") as data:
    blob_client.upload_blob(data)

print("Backup complete")
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# MYSQL DB BACKUP IN RUNNING MYSQL DOCKER 
#!/bin/bash

# ================== CONFIG ==================
CONTAINER_NAME="mysql-container"         # MySQL Docker container name
MYSQL_USER="root"                         # MySQL username
MYSQL_PASSWORD="yourpassword"             # MySQL password
BACKUP_DIR="/var/backups/mysql"           # Local backup directory
AZURE_STORAGE_ACCOUNT="yourstorageaccount"
AZURE_CONTAINER="mysql-backups"
SAS_TOKEN=''

# ================== SCRIPT ==================
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
mkdir -p "$BACKUP_DIR"

echo "[INFO] Backing up MySQL databases from container $CONTAINER_NAME..."

# Dump all databases and compress
docker exec "$CONTAINER_NAME" sh -c "exec mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD --all-databases" \
    | gzip > "$BACKUP_DIR/mysql-all-$TIMESTAMP.sql.gz"

if [ $? -ne 0 ]; then
    echo "[ERROR] mysqldump failed!"
    exit 1
fi

echo "[INFO] Uploading backup to Azure Blob Storage..."
azcopy copy "$BACKUP_DIR/mysql-all-$TIMESTAMP.sql.gz" \
    "https://$AZURE_STORAGE_ACCOUNT.blob.core.windows.net/$AZURE_CONTAINER/mysql-all-$TIMESTAMP.sql.gz$SAS_TOKEN" \
    --overwrite=true

if [ $? -eq 0 ]; then
    echo "[INFO] Backup successfully uploaded."
else
    echo "[ERROR] AzCopy upload failed!"
    exit 1
fi

# Cleanup local backups older than 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete
echo "[INFO] Old backups cleaned up. Backup completed successfully."
