#!/usr/bin/env sh
# İT Laboratoriyası — 3D Dizayner  (Linux / macOS)
#
# Lokal server qaldırır və brauzeri açır. Server MÜTLƏQDİR: index.html-i
# birbaşa açanda brauzer file:// rejimində CORS səbəbindən assets/ qovluğundakı
# teksturaları və HDRI-ni yükləmir — səhnə boz və işıqsız görünür.
#
# Windows üçün: BASLAT.bat

cd "$(dirname "$0")" || exit 1

PY=$(command -v python3 || command -v python) || {
  echo "  Python tapılmadı. python3 quraşdırın."
  exit 1
}

PORT=8123
URL="http://localhost:$PORT"

if   command -v xdg-open >/dev/null 2>&1; then OPEN=xdg-open
elif command -v open     >/dev/null 2>&1; then OPEN=open
else OPEN=""
fi

echo
echo "  İT Laboratoriyası — 3D Dizayner"
echo "  ================================"
echo

"$PY" -m http.server "$PORT" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' INT TERM

sleep 1
if ! kill -0 "$SRV" 2>/dev/null; then
  echo "  Server qalxmadı — $PORT portu məşğul ola bilər."
  echo "  Yoxlayın:  $URL"
  exit 1
fi

echo "  Server işləyir:  $URL"
echo "  Dayandırmaq üçün Ctrl+C"
echo
[ -n "$OPEN" ] && "$OPEN" "$URL" >/dev/null 2>&1

wait $SRV
