#!/bin/bash
# ============================================
# Security Audit Script untuk 90twin.com
# Jalankan dari terminal lokal Anda
# ============================================

TARGET="90twin.com"
URL="https://90twin.com"
REPORT="security_report_$(date +%Y%m%d_%H%M%S).txt"

echo "============================================" | tee $REPORT
echo "  SECURITY AUDIT: $TARGET" | tee -a $REPORT
echo "  Tanggal: $(date)" | tee -a $REPORT
echo "============================================" | tee -a $REPORT

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

# ---- 1. DNS & IP INFO ----
echo -e "\n[1] DNS & IP INFO" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
nslookup $TARGET 2>/dev/null | tee -a $REPORT || dig $TARGET 2>/dev/null | tee -a $REPORT
echo "" | tee -a $REPORT
echo "IP Address:" | tee -a $REPORT
host $TARGET 2>/dev/null | tee -a $REPORT

# ---- 2. SSL/TLS AUDIT ----
echo -e "\n[2] SSL/TLS CERTIFICATE" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
echo | openssl s_client -connect $TARGET:443 -servername $TARGET 2>/dev/null | openssl x509 -noout -text 2>/dev/null | grep -E "(Subject|Issuer|Not Before|Not After|DNS:|Public Key Algorithm|Public-Key)" | tee -a $REPORT

echo -e "\n[2b] SSL/TLS VERSION & CIPHERS (nmap)" | tee -a $REPORT
if command -v nmap &>/dev/null; then
  nmap --script ssl-enum-ciphers -p 443 $TARGET 2>/dev/null | tee -a $REPORT
else
  echo "nmap tidak ditemukan - skip cipher check" | tee -a $REPORT
fi

# ---- 3. SECURITY HEADERS ----
echo -e "\n[3] HTTP SECURITY HEADERS" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
HEADERS=$(curl -sk -D - "$URL/" -A "$UA" -o /dev/null 2>&1)
echo "$HEADERS" | tee -a $REPORT

echo -e "\n[3b] SECURITY HEADER CHECKLIST:" | tee -a $REPORT
for header in "Strict-Transport-Security" "Content-Security-Policy" "X-Frame-Options" "X-Content-Type-Options" "Referrer-Policy" "Permissions-Policy" "X-XSS-Protection"; do
  if echo "$HEADERS" | grep -qi "$header"; then
    val=$(echo "$HEADERS" | grep -i "$header" | head -1)
    echo "  [OK] $val" | tee -a $REPORT
  else
    echo "  [MISSING] $header" | tee -a $REPORT
  fi
done

# ---- 4. COMMON SENSITIVE FILES ----
echo -e "\n[4] SENSITIVE FILES & PATHS" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
PATHS=(
  "/.env" "/.env.local" "/.env.production" "/.env.backup"
  "/config.js" "/config.json" "/config.php"
  "/.git/HEAD" "/.git/config"
  "/wp-admin" "/wp-login.php"
  "/phpinfo.php" "/info.php"
  "/admin" "/administrator"
  "/api" "/api/v1" "/api/v2" "/api/docs" "/api/swagger"
  "/swagger.json" "/swagger-ui.html" "/openapi.json"
  "/graphql" "/graphiql"
  "/server-status" "/server-info"
  "/backup" "/backup.zip" "/backup.sql" "/dump.sql"
  "/robots.txt" "/sitemap.xml"
  "/crossdomain.xml" "/clientaccesspolicy.xml"
)

for path in "${PATHS[@]}"; do
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$URL$path" -A "$UA")
  size=$(curl -sk -w "%{size_download}" -o /dev/null "$URL$path" -A "$UA")
  if [[ "$code" == "200" ]]; then
    echo "  [FOUND 200] $path (size: ${size}b)" | tee -a $REPORT
  elif [[ "$code" == "301" || "$code" == "302" ]]; then
    loc=$(curl -sk -D - "$URL$path" -A "$UA" -o /dev/null | grep -i "location:" | head -1)
    echo "  [REDIRECT $code] $path -> $loc" | tee -a $REPORT
  elif [[ "$code" != "404" && "$code" != "403" && "$code" != "000" ]]; then
    echo "  [HTTP $code] $path" | tee -a $REPORT
  fi
done

# ---- 5. CORS CHECK ----
echo -e "\n[5] CORS CONFIGURATION" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
CORS=$(curl -sk -D - "$URL/" -A "$UA" \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: GET" \
  -o /dev/null 2>&1 | grep -i "Access-Control")
if echo "$CORS" | grep -qi "Access-Control-Allow-Origin: \*"; then
  echo "  [VULN] CORS terlalu permisif: Allow-Origin: *" | tee -a $REPORT
elif echo "$CORS" | grep -qi "Access-Control-Allow-Origin: https://evil.com"; then
  echo "  [VULN] CORS reflect origin - BERBAHAYA!" | tee -a $REPORT
elif [ -z "$CORS" ]; then
  echo "  [INFO] Tidak ada CORS header (mungkin tidak diperlukan)" | tee -a $REPORT
else
  echo "  [OK] $CORS" | tee -a $REPORT
fi

# ---- 6. CLICKJACKING CHECK ----
echo -e "\n[6] CLICKJACKING CHECK" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
XFO=$(curl -sk -D - "$URL/" -A "$UA" -o /dev/null | grep -i "X-Frame-Options\|frame-ancestors")
if [ -z "$XFO" ]; then
  echo "  [VULN] Tidak ada X-Frame-Options atau CSP frame-ancestors - Rentan Clickjacking!" | tee -a $REPORT
else
  echo "  [OK] $XFO" | tee -a $REPORT
fi

# ---- 7. COOKIE FLAGS ----
echo -e "\n[7] COOKIE SECURITY FLAGS" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
COOKIES=$(curl -sk -c - "$URL/" -A "$UA" | grep -v "^#" | grep -v "^$")
if [ -n "$COOKIES" ]; then
  echo "$COOKIES" | while read line; do
    name=$(echo "$line" | awk '{print $6}')
    if ! echo "$line" | grep -qi "HttpOnly"; then
      echo "  [WARN] Cookie '$name' missing HttpOnly flag" | tee -a $REPORT
    fi
    if ! echo "$line" | grep -qi "Secure"; then
      echo "  [WARN] Cookie '$name' missing Secure flag" | tee -a $REPORT
    fi
    if ! echo "$line" | grep -qi "SameSite"; then
      echo "  [WARN] Cookie '$name' missing SameSite flag (CSRF risk)" | tee -a $REPORT
    fi
  done
else
  echo "  [INFO] Tidak ada cookie yang ditemukan di response awal" | tee -a $REPORT
fi

# ---- 8. INFORMATION DISCLOSURE ----
echo -e "\n[8] SERVER INFORMATION DISCLOSURE" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
SERVER=$(curl -sk -D - "$URL/" -A "$UA" -o /dev/null | grep -iE "^Server:|^X-Powered-By:|^X-AspNet-Version:|^X-Generator:|^Via:")
if [ -n "$SERVER" ]; then
  echo "  [INFO LEAK] $SERVER" | tee -a $REPORT
else
  echo "  [OK] Tidak ada server banner yang bocor" | tee -a $REPORT
fi

# ---- 9. HTTP METHODS ----
echo -e "\n[9] ALLOWED HTTP METHODS" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
for method in GET POST PUT DELETE PATCH OPTIONS TRACE; do
  code=$(curl -sk -X $method -o /dev/null -w "%{http_code}" "$URL/" -A "$UA")
  echo "  $method -> HTTP $code" | tee -a $REPORT
done

# ---- 10. SUBDOMAINS ----
echo -e "\n[10] COMMON SUBDOMAINS" | tee -a $REPORT
echo "----------------------------" | tee -a $REPORT
for sub in www api admin dev staging test mail ftp smtp pop vpn cdn static assets; do
  result=$(host $sub.$TARGET 2>/dev/null | grep "has address")
  if [ -n "$result" ]; then
    echo "  [FOUND] $result" | tee -a $REPORT
  fi
done

echo -e "\n============================================" | tee -a $REPORT
echo "  AUDIT SELESAI - Report: $REPORT" | tee -a $REPORT
echo "============================================" | tee -a $REPORT
