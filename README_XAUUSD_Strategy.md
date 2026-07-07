# XAUUSD M5 + M15 Confirmation Entry — Panduan Pakai

Pine Script indicator untuk TradingView yang memberi sinyal entry XAUUSD berdasarkan
bias M15, timing M5, dan candle konfirmasi. TradingView yang memantau chart 24/7 dan
mengirim alert ke HP/desktop Anda — bukan Claude.

## Cara Pasang di TradingView

1. Buka TradingView → chart **XAUUSD** → set timeframe **M5**.
2. Klik menu **Pine Editor** di bawah chart.
3. Copy seluruh isi `xauusd_m5m15_confirmation.pine`, paste, klik **Save** → beri nama.
4. Klik **Add to chart**.

## Cara Bikin Alert (biar TradingView notifikasi otomatis)

1. Klik ikon jam (**Alert**) di toolbar atas.
2. **Condition**: pilih indicator ini → pilih salah satu:
   - `XAUUSD LONG entry`
   - `XAUUSD SHORT entry`
   - `XAUUSD ANY entry` (gabungan)
3. **Options**: pilih **Once Per Bar Close** (WAJIB — sinyal hanya valid setelah candle close).
4. **Notifications**: aktifkan **Push notification** (untuk app TV di HP), Email, atau Webhook.
5. Simpan.

TradingView akan kirim notifikasi ke HP Anda tiap kali sinyal LONG/SHORT muncul.
Alert perlu paket berbayar TradingView (Essential ke atas) untuk aktif >1 alert simultan.

## Logika Strategi

| Elemen | Aturan |
|---|---|
| **Bias (M15)** | EMA50 > EMA200 dan close > EMA50 → **Bullish**. Kebalikannya → **Bearish**. |
| **Timing (M5)** | Harga pullback ke area EMA20 M5 (dalam N×ATR) |
| **Konfirmasi**  | **Engulfing** (body candle telan candle sebelumnya) **ATAU** **Pin Bar** (wick ≥ 2× body, searah bias) |
| **Filter ATR**  | ATR M5 ≥ nilai minimum (default 1.5 USD) — hindari market sepi |
| **Filter Sesi** | Default 13:00–23:59 waktu chart (London + NY overlap) |
| **Entry**       | Close candle konfirmasi |
| **SL**          | Low/high candle konfirmasi ± buffer ATR (default 0.3× ATR) |
| **TP**          | Entry ± (Risk × RR ratio), default RR 1:2 |

## Parameter yang Bisa Di-tune

Semua bisa diubah dari panel setting indicator (klik ikon roda gigi):
- Panjang EMA (bias & pullback)
- Toleransi pullback (x ATR)
- Aktif/matikan Engulfing atau Pin Bar
- Rasio wick/body pin bar
- Buffer SL dan RR ratio
- ATR minimum & jam sesi

## Peringatan Penting

- **Ini bukan Holy Grail**. Backtest dulu di TradingView **Strategy Tester** (versi
  strategy bisa dibuat dari indicator ini dengan menambahkan `strategy.entry`).
- **Selalu manajemen risiko** — max 1–2% dari equity per trade.
- **Sinyal palsu bisa muncul** saat news besar (NFP, FOMC, CPI). Pertimbangkan filter kalender.
- **Broker spread & slippage** bisa mengubah RR real. Uji forward di akun demo dulu.

## Strategy Tester Version — `xauusd_m5m15_strategy.pine`

Versi `strategy()` untuk backtest di TradingView Strategy Tester.

**Cara pakai:**
1. Buka Pine Editor → paste isi `xauusd_m5m15_strategy.pine` → **Save** → **Add to chart**.
2. Buka tab **Strategy Tester** di bawah chart.
3. Cek **Overview** (net profit, drawdown, win rate), **Performance Summary**, **List of Trades**.
4. Tune input via ikon roda gigi indicator, jalankan ulang.

**Tambahan dibanding versi indicator:**
- Risk sizing otomatis — `Risk per trade (%)` menghitung `qty` dari equity & stop distance.
- `strategy.exit` pasang OCO order SL + TP (RR ratio dari input).
- Filter window backtest (`Backtest From/To`).
- `commission_value` + `slippage` disetel supaya backtest lebih realistis untuk XAUUSD.
- Setiap entry memicu `alert()` dengan JSON payload — kompatibel dengan Telegram bridge di bawah.

## Webhook → Telegram Bot — `telegram_bridge/`

Server Python kecil yang menerima webhook TradingView dan forward ke Telegram.

**Arsitektur:**

```
TradingView Alert (Pro+)  --HTTPS POST-->  webhook_server.py  --Bot API-->  Telegram
                             ?secret=…                          sendMessage      chat/channel
```

**Setup:**

1. **Bikin Telegram bot**
   - Chat `@BotFather` di Telegram → `/newbot` → catat **bot token**.
   - Chat `@userinfobot` → catat **chat_id** Anda (atau id channel/group).

2. **Deploy server** (contoh: Docker, Railway, Fly.io, VPS)
   ```bash
   cd telegram_bridge
   cp .env.example .env      # isi TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_SECRET
   docker build -t tv-bridge .
   docker run -d --name tv-bridge --env-file .env -p 8080:8080 tv-bridge
   ```
   Atau tanpa Docker:
   ```bash
   pip install -r requirements.txt
   export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... WEBHOOK_SECRET=...
   gunicorn -b 0.0.0.0:8080 webhook_server:app
   ```
   Server harus punya HTTPS URL publik (Cloudflare Tunnel / ngrok / hosting mana pun) —
   TradingView tidak mau webhook ke IP mentah tanpa HTTPS.

3. **Konfigurasi alert TradingView**
   - Di dialog Alert → **Notifications** → centang **Webhook URL**:
     ```
     https://your-domain.com/webhook?secret=<WEBHOOK_SECRET yang sama>
     ```
   - **Message**: sudah otomatis dari `alert(...)` di indicator/strategy — JSON
     seperti `{"symbol":"XAUUSD","side":"LONG","price":2345.6,"sl":2340.1,"tp":2356.6}`.
   - Untuk versi indicator, ganti alert message dengan payload JSON tersebut manual.

4. **Test**
   ```bash
   curl -X POST "https://your-domain.com/webhook?secret=..." \
        -H "Content-Type: application/json" \
        -d '{"symbol":"XAUUSD","side":"LONG","price":2345.6,"sl":2340.1,"tp":2356.6}'
   ```
   Anda akan menerima pesan di Telegram.

**Fitur server:**
- Validasi shared secret via `?secret=` atau header `X-Webhook-Secret` (constant-time compare).
- Dedup 30 detik — kalau TradingView kirim ganda, hanya satu diteruskan.
- Health check di `GET /health`.
- Fallback ke raw text kalau payload bukan JSON.
- Self-test: `python test_webhook.py`.

**Peringatan keamanan:**
- **Selalu pakai HTTPS** — token bot dan sinyal Anda kirim di dalamnya.
- **Rotasi `WEBHOOK_SECRET`** kalau bocor.
- Jangan commit file `.env` — sudah di-gitignore lewat pola default; tetap cek `git status` sebelum push.
- Server ini **hanya** forward pesan. Untuk auto-execute order ke MT5/broker, butuh
  bridge terpisah (misalnya python MetaTrader5 API atau AutoView) — tanya kalau mau
  saya lanjutkan ke sana.

## Opsi Lanjutan

- **Auto-execute** ke MT5/cTrader (butuh bridge terpisah, **berisiko tinggi**, hanya
  setelah backtest matang).
- **Multi-symbol** — extend strategy untuk pantau XAUUSD + XAGUSD + BTCUSD simultan.
- **News filter** — integrasi kalender ekonomi (Forex Factory RSS) untuk skip jam news.
- **Trailing stop** — SL geser ikut harga setelah profit tertentu.
