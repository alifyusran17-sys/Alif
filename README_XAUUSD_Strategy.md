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

## Kalau Mau Otomatisasi Lebih Jauh

Opsi lanjutan (bilang saja mana yang mau saya kerjakan):

1. **Ubah jadi Strategy** — versi `strategy()` biar bisa backtest otomatis dengan
   equity curve, win rate, max drawdown.
2. **Webhook → Telegram bot** — alert TradingView diteruskan ke bot Telegram sendiri
   biar formatnya custom, atau ke server yang eksekusi order via MT5/broker API.
3. **Auto-execute** — sambungkan ke MT5 / cTrader via bridge (mis. TradingConnector,
   AutoView). Ini butuh setup terpisah dan **berisiko tinggi** — hanya rekomendasikan
   setelah backtest matang.
