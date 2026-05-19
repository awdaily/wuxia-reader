# Wuxia Reader

แปลนิยายกำลังภายในจาก lnmtl.com เป็นภาษาไทยสไตล์กำลังภายใน ผ่าน ai.maoy.cn API

## โครงสร้าง

```
wuxia-reader/
├── api/fetch.py        # Vercel serverless (Python) — ดึงนิยายจาก lnmtl.com
├── index.html          # หน้าเว็บ + เรียก translate API ตรงจาก browser
├── dev.py              # Flask สำหรับเทสต์ local เท่านั้น
├── requirements.txt    # deps สำหรับ api/fetch.py
└── vercel.json         # บังคับ build config
```

## Local dev

```bash
pip install -r requirements.txt flask
python dev.py
# เปิด http://localhost:5000
```

## Deploy to Vercel via GitHub

1. สร้าง repo ใหม่บน GitHub
2. Push โค้ดขึ้น
3. ไปที่ https://vercel.com/new → Import Git Repository → เลือก repo
4. กด Deploy

Vercel auto-deploy ทุกครั้งที่ push ขึ้น `main`

## วิธีใช้

- ใส่ API Key จาก ai.maoy.cn
- เลือก model (default: gpt-5.4)
- วาง URL ตอนจาก lnmtl.com
- กด โหลด

## หมายเหตุ

- `/api/fetch` (Python serverless) ดึง HTML จาก lnmtl.com เพราะ browser ติด CORS
- Translate API เรียกตรงจาก browser ไป ai.maoy.cn → ไม่ติด Vercel timeout
- API Key เก็บใน localStorage ของ browser เท่านั้น
