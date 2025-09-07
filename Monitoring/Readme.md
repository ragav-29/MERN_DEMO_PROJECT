mkdir grafana
mkdir loki
mkdir promtail
touch docker-compose.yml
nano docker-compose.yml # copy the contents from below
ls
docker-compose up -d --force-recreate # be sure you've created promtail-config.yml and loki-config.yml before running this
