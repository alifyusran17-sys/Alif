# Bot Sinyal XAUUSD M5 → Telegram

Bot ini memantau chart **XAUUSD timeframe M5** setiap candle close, lalu mengirim
alert **entry (BUY/SELL) lengkap dengan SL, TP1, TP2** ke Telegram Anda. Anda
tinggal eksekusi manual di aplikasi **Exness mobile**.

> ⚠️ **Disclaimer**: Sinyal bersifat informasi/edukasi, bukan saran keuangan.
> Tidak ada strategi yang menjamin profit. Selalu gunakan manajemen risiko
> (maksimal 1–2% modal per posisi) dan uji dulu di akun demo.

## Strategi

Setiap candle M5 yang sudah close dievaluasi:

| Komponen | Aturan |
|---|---|
| Filter tren | BUY hanya jika harga > EMA200 **dan** EMA50 > EMA200 (SELL kebalikannya) |
| Trigger entry | EMA9 crossing EMA21 searah tren |
| Konfirmasi | RSI(14) 50–70 untuk BUY, 30–50 untuk SELL |
| Stop Loss | 1.5 × ATR(14) |
| Take Profit | TP1 = 1.5 × ATR (RR 1:1), TP2 = 3 × ATR (RR 1:2) |
| Anti-spam | Cooldown 6 candle (30 menit) setelah sinyal |

Bot otomatis skip saat pasar tutup (akhir pekan & jeda harian 21:00–22:00 UTC).

## Persiapan (semua gratis)

### 1. Buat bot Telegram
1. Buka Telegram, chat ke **@BotFather** → kirim `/newbot` → ikuti instruksi.
2. Simpan **token** yang diberikan (format `123456:ABC-xxxx`).
3. Kirim pesan apa saja ke bot baru Anda (misal "halo").
4. Buka `https://api.telegram.org/bot<TOKEN>/getUpdates` di browser,
   cari `"chat":{"id":123456789}` → itu **chat_id** Anda.

### 2. Ambil API key data harga
1. Daftar gratis di [twelvedata.com](https://twelvedata.com) (free tier:
   800 request/hari — bot hanya butuh ±288/hari).
2. Salin **API key** dari dashboard.

### 3. Deploy ke Render (cloud gratis)
1. Daftar di [render.com](https://render.com) (login pakai GitHub).
2. **New → Web Service** → hubungkan repo ini.
3. Render otomatis membaca `render.yaml` (Blueprint), atau isi manual:
   - Root Directory: `xauusd-signal-bot`
   - Build: `pip install -r requirements.txt`
   - Start: `python main.py`
   - Plan: **Free**
4. Isi Environment Variables:
   - `TWELVEDATA_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Deploy. Kalau berhasil, bot mengirim pesan "🤖 Bot sinyal ... aktif" ke Telegram.

### 4. Keep-alive (penting!)
Free tier Render menidurkan service setelah ±15 menit tanpa traffic.
Solusi: daftar gratis di [uptimerobot.com](https://uptimerobot.com) →
buat monitor **HTTP(s)** ke URL Render Anda (misal
`https://xauusd-signal-bot.onrender.com/`) dengan interval **5 menit**.
Ini membuat bot tetap bangun 24 jam.

## Menjalankan lokal (opsional, untuk tes)

```bash
cd xauusd-signal-bot
pip install -r requirements.txt
export TWELVEDATA_API_KEY=xxx
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python main.py
```

Cek status bot kapan saja lewat browser: buka URL service Anda —
tampil JSON berisi candle terakhir yang dicek dan sinyal terakhir.

## Konfigurasi opsional (env vars)

| Variabel | Default | Keterangan |
|---|---|---|
| `SYMBOL` | `XAU/USD` | Bisa diganti pair lain yang didukung Twelve Data |
| `COOLDOWN_CANDLES` | `6` | Jarak minimal antar sinyal (dalam candle) |
| `PORT` | `10000` | Port web service (Render mengisi otomatis) |

## Catatan harga Exness

Data harga dari Twelve Data adalah harga pasar spot agregat; bisa berbeda
beberapa puluh sen dengan quote Exness (spread/markup broker). Gunakan level
Entry/SL/TP sebagai acuan, lalu sesuaikan dengan harga aktual di app Exness
saat eksekusi.
