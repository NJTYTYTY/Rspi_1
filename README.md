# 🦐 Shrimp Farm Cloud Controller

ระบบควบคุมการยกเชือกและถ่ายรูปในบ่อกุ้งผ่าน Cloud API

## 📁 โครงสร้างโปรเจค

```
/project
├── cloud_app.py         # deploy ไป cloud (public API)
├── controller.py         # รันบน Raspberry Pi
├── sensor.py            # รันบน Raspberry Pi (auto-run ตอน boot)
├── requirements.txt     # รวม lib ของทั้ง cloud และ Pi
├── railway.json         # config สำหรับ Railway deploy
└── README.md
```

## 🔄 Flow การทำงาน

1. **Cloud App** (deploy บน Railway) - รับคำสั่งจาก user แล้วเก็บไว้
2. **Raspberry Pi** - วน loop ถาม cloud ว่ามีงานมั้ย ถ้ามีก็ทำงานยกเชือก+ถ่ายรูป

## 🚀 การ Deploy

### 1. Deploy Cloud App บน Railway

1. สร้างโปรเจคใหม่บน [Railway](https://railway.app)
2. Connect GitHub repository
3. Railway จะ auto-detect `railway.json` และ deploy `cloud_app.py`
4. จำ URL ที่ได้ เช่น `https://your-app.railway.app`

### 2. ตั้งค่า Raspberry Pi

1. อัปเดต `CLOUD_API_URL` ใน `controller.py`:
   ```python
   CLOUD_API_URL = "https://your-app.railway.app"  # เปลี่ยนเป็น URL จริง
   ```

2. ติดตั้ง dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. รัน controller.py:
   ```bash
   python controller.py
   ```

4. (Optional) ตั้งเป็น systemd service ให้รันอัตโนมัติ

## 📡 API Endpoints

### Cloud App (Railway)

- `POST /lift` - ส่งคำสั่งยกเชือก
- `GET /job/{pond_id}` - Pi ถามว่ามีงานมั้ย
- `POST /job/{pond_id}/complete` - Pi แจ้งงานเสร็จ
- `GET /status` - ดูสถานะระบบ
- `GET /health` - Health check

### ตัวอย่างการใช้งาน

#### 1. ส่งคำสั่งยกเชือก
```bash
curl -X POST "https://your-app.railway.app/lift" \
  -H "Content-Type: application/json" \
  -d '{"pond_id": 1, "action": "lift"}'
```

#### 2. ตรวจสอบสถานะ
```bash
curl "https://your-app.railway.app/status"
```

## ⚙️ การตั้งค่า

### Cloud App
- เปลี่ยน `CLOUD_API_URL` ใน `controller.py`
- เปลี่ยน `BACKEND_URL` ใน `controller.py` (สำหรับส่งไฟล์)

### Raspberry Pi
- ตั้งค่า `POND_ID` ใน `controller.py`
- ตั้งค่า GPIO pins ตามฮาร์ดแวร์
- ตั้งค่า `JOB_CHECK_INTERVAL` (วินาที)

## 🔧 Hardware Requirements

### Raspberry Pi
- GPIO pins สำหรับมอเตอร์ (PWM, INA, INB)
- Limit switch
- Distance sensor (ADS1115)
- Camera module
- Temperature sensor (DS18B20)

## 📝 Logs

- Cloud App: ดูใน Railway dashboard
- Raspberry Pi: `/tmp/controller_debug.log`

## 🐛 Troubleshooting

1. **Pi ไม่สามารถเชื่อมต่อ Cloud**
   - ตรวจสอบ internet connection
   - ตรวจสอบ `CLOUD_API_URL`

2. **Cloud ไม่ตอบสนอง**
   - ตรวจสอบ Railway deployment
   - ดู logs ใน Railway dashboard

3. **มอเตอร์ไม่ทำงาน**
   - ตรวจสอบ GPIO connections
   - ตรวจสอบ power supply

## 📞 Support

หากมีปัญหาติดต่อทีมพัฒนา
