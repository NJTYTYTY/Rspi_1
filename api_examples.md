# 🚀 API Examples - Shrimp Farm Cloud Controller

## 📡 Cloud App Endpoints

### 1. ส่งคำสั่งยกยอขึ้น (Frontend)
```bash
curl -X POST "https://your-railway-app.railway.app/lift-up" \
  -H "Content-Type: application/json" \
  -d '{
    "pondId": "1",
    "action": "lift_up",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "คำสั่งยกยอขึ้นสำหรับบ่อ 1 ถูกบันทึกแล้ว",
  "job_id": 1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 2. ส่งคำสั่งยกยอลง (Frontend)
```bash
curl -X POST "https://your-railway-app.railway.app/lift-down" \
  -H "Content-Type: application/json" \
  -d '{
    "pondId": "1",
    "action": "lift_down",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "คำสั่งยกยอลงสำหรับบ่อ 1 ถูกบันทึกแล้ว",
  "job_id": 1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 3. ส่งคำสั่งยกเชือกแบบเดิม (Pi)
```bash
curl -X POST "https://your-railway-app.railway.app/lift" \
  -H "Content-Type: application/json" \
  -d '{
    "pond_id": 1,
    "action": "lift",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }'
```

### 4. ตรวจสอบสถานะ
```bash
curl "https://your-railway-app.railway.app/status"
```

**Response:**
```json
{
  "pending_jobs": 1,
  "completed_jobs": 0,
  "pending_job_list": [1],
  "completed_job_list": [],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 🔄 Flow การทำงาน

### Frontend → Cloud App → Raspberry Pi

1. **Frontend** ส่งคำสั่ง:
   - `POST /lift-up` - ยกยอขึ้น
   - `POST /lift-down` - ยกยอลง

2. **Cloud App** เก็บงานไว้ใน `pending_jobs`

3. **Raspberry Pi** วน loop:
   - `GET /job/{pond_id}` - ถามว่ามีงานมั้ย
   - ถ้ามีงาน → ทำงานตาม action
   - `POST /job/{pond_id}/complete` - แจ้งเสร็จ

## 🎯 Action Types

| Action | Description | Pi Behavior |
|--------|-------------|-------------|
| `lift_up` | ยกยอขึ้น + ถ่ายรูป | ยกขึ้น รอ limit switch หยุด + ถ่ายรูป 5 วินาที (ค้างไว้) |
| `lift_down` | ยกยอลงเท่านั้น | ยกลง 5 วินาที หยุด (ไม่ถ่ายรูป) |
| `lift` | ยกเชือกแบบเดิม | ยกขึ้น + ถ่ายรูป + ยกลง |

## 📝 Frontend Integration

### เปลี่ยน URL ใน Frontend:
```javascript
// เปลี่ยนจาก
const backendMiddleUrl = process.env.NEXT_PUBLIC_RSPI_SERVER_YOKYOR || 'http://localhost:3002/api'

// เป็น
const cloudApiUrl = process.env.NEXT_PUBLIC_CLOUD_API_URL || 'https://your-railway-app.railway.app'
```

### เปลี่ยน Endpoint:
```javascript
// เปลี่ยนจาก
const response = await fetch(`${backendMiddleUrl}/${endpoint}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestBody)
})

// เป็น
const response = await fetch(`${cloudApiUrl}/lift-up`, {  // หรือ lift-down
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    pondId: pondIdString,
    action: "lift_up",  // หรือ "lift_down"
    timestamp: new Date().toISOString()
  })
})
```
