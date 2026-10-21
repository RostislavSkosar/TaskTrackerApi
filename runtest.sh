#!/bin/bash
# Сборка и запуск API + выполнение серии проверочных HTTP-запросов.
# Использование: bash runtest.sh   (из каталога Lab_WebAPI)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Каталог с установленным .NET SDK (в данной лабораторной SDK распакован рядом с проектом)
DOTNET_HOME="${HOME}/.dotnet"
[ -x "${DOTNET_HOME}/dotnet" ] || DOTNET_HOME="$(dirname "${ROOT}")/.dotnet"
[ -x "${DOTNET_HOME}/dotnet" ] || DOTNET_HOME="${ROOT}/.dotnet"

export DOTNET_ROOT="${DOTNET_HOME}"
export PATH="${PATH}:${DOTNET_HOME}"
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

cd "${ROOT}/src/TaskTrackerApi" || exit 9
dotnet build -c Release -v q 2>&1 | tail -5

ASPNETCORE_URLS=http://127.0.0.1:5080 nohup dotnet bin/Release/net8.0/TaskTrackerApi.dll > /tmp/api.log 2>&1 &
SRV=$!

UP=0
for i in $(seq 1 40); do
  if python3 -c "
import urllib.request, sys
try:
    urllib.request.urlopen('http://127.0.0.1:5080/api/projects', timeout=2); sys.exit(0)
except Exception: sys.exit(1)
"; then
    echo "SERVER UP after ${i}s"; UP=1; break
  fi
  sleep 1
done

if [ "${UP}" = "0" ]; then
  echo "SERVER FAILED TO START"; tail -30 /tmp/api.log; kill ${SRV} 2>/dev/null; exit 1
fi

cd "${ROOT}/report" || exit 9
python3 test_requests.py

kill ${SRV} 2>/dev/null
echo "=== api log tail ==="
tail -6 /tmp/api.log
