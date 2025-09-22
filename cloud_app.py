from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import json
import os

app = FastAPI(title="Shrimp Farm Cloud Controller", version="1.0.0")

# === DATA MODELS ===
class LiftCommand(BaseModel):
    pond_id: int
    action: str = "lift"  # lift, status
    timestamp: Optional[str] = None

class LiftUpCommand(BaseModel):
    pondId: str  # frontend ส่งมาเป็น string
    action: str = "lift_up"
    timestamp: Optional[str] = None

class LiftDownCommand(BaseModel):
    pondId: str  # frontend ส่งมาเป็น string
    action: str = "lift_down"
    timestamp: Optional[str] = None

class JobResponse(BaseModel):
    has_job: bool
    job_data: Optional[Dict[str, Any]] = None
    message: str

# === IN-MEMORY STORAGE ===
# ใน production ควรใช้ database แทน
pending_jobs: Dict[int, Dict[str, Any]] = {}
completed_jobs: Dict[int, Dict[str, Any]] = {}

# === API ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "message": "Shrimp Farm Cloud Controller API",
        "version": "1.0.0",
        "endpoints": {
            "POST /lift": "ส่งคำสั่งยกเชือก (Pi)",
            "POST /lift-up": "ส่งคำสั่งยกยอขึ้น (Frontend)",
            "POST /lift-down": "ส่งคำสั่งยกยอลง (Frontend)",
            "GET /job/{pond_id}": "Pi ถามว่ามีงานมั้ย",
            "POST /job/{pond_id}/complete": "Pi แจ้งงานเสร็จ",
            "GET /status": "ดูสถานะระบบ"
        }
    }

@app.post("/lift")
async def create_lift_command(command: LiftCommand):
    """User ส่งคำสั่งยกเชือกมา"""
    try:
        # เพิ่ม timestamp ถ้าไม่มี
        if not command.timestamp:
            command.timestamp = datetime.now().isoformat()
        
        # เก็บงานไว้ใน pending_jobs
        job_data = {
            "pond_id": command.pond_id,
            "action": command.action,
            "timestamp": command.timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        pending_jobs[command.pond_id] = job_data
        
        print(f"📝 รับคำสั่งยกเชือกสำหรับบ่อ {command.pond_id} เรียบร้อย")
        
        return {
            "success": True,
            "message": f"คำสั่งยกเชือกสำหรับบ่อ {command.pond_id} ถูกบันทึกแล้ว",
            "job_id": command.pond_id,
            "timestamp": command.timestamp
        }
        
    except Exception as e:
        print(f"❌ Error ในการรับคำสั่ง: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/lift-up")
async def create_lift_up_command(command: LiftUpCommand):
    """Frontend ส่งคำสั่งยกยอขึ้นมา"""
    try:
        # แปลง pondId เป็น int
        pond_id = int(command.pondId)
        
        # เพิ่ม timestamp ถ้าไม่มี
        if not command.timestamp:
            command.timestamp = datetime.now().isoformat()
        
        # เก็บงานไว้ใน pending_jobs
        job_data = {
            "pond_id": pond_id,
            "action": command.action,
            "timestamp": command.timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        pending_jobs[pond_id] = job_data
        
        print(f"📝 รับคำสั่งยกยอขึ้นสำหรับบ่อ {pond_id} เรียบร้อย")
        
        return {
            "success": True,
            "message": f"คำสั่งยกยอขึ้นสำหรับบ่อ {pond_id} ถูกบันทึกแล้ว",
            "job_id": pond_id,
            "timestamp": command.timestamp
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="pondId ต้องเป็นตัวเลข")
    except Exception as e:
        print(f"❌ Error ในการรับคำสั่งยกยอขึ้น: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/lift-down")
async def create_lift_down_command(command: LiftDownCommand):
    """Frontend ส่งคำสั่งยกยอลงมา"""
    try:
        # แปลง pondId เป็น int
        pond_id = int(command.pondId)
        
        # เพิ่ม timestamp ถ้าไม่มี
        if not command.timestamp:
            command.timestamp = datetime.now().isoformat()
        
        # เก็บงานไว้ใน pending_jobs
        job_data = {
            "pond_id": pond_id,
            "action": command.action,
            "timestamp": command.timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        pending_jobs[pond_id] = job_data
        
        print(f"📝 รับคำสั่งยกยอลงสำหรับบ่อ {pond_id} เรียบร้อย")
        
        return {
            "success": True,
            "message": f"คำสั่งยกยอลงสำหรับบ่อ {pond_id} ถูกบันทึกแล้ว",
            "job_id": pond_id,
            "timestamp": command.timestamp
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="pondId ต้องเป็นตัวเลข")
    except Exception as e:
        print(f"❌ Error ในการรับคำสั่งยกยอลง: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.get("/job/{pond_id}")
async def get_job(pond_id: int):
    """Pi ถามว่ามีงานสำหรับบ่อนี้มั้ย"""
    try:
        if pond_id in pending_jobs:
            job = pending_jobs[pond_id]
            print(f"📤 ส่งงานให้บ่อ {pond_id}: {job}")
            
            return JobResponse(
                has_job=True,
                job_data=job,
                message=f"มีงานสำหรับบ่อ {pond_id}"
            )
        else:
            return JobResponse(
                has_job=False,
                job_data=None,
                message=f"ไม่มีงานสำหรับบ่อ {pond_id}"
            )
            
    except Exception as e:
        print(f"❌ Error ในการตรวจสอบงาน: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/job/{pond_id}/complete")
async def complete_job(pond_id: int, result: Dict[str, Any]):
    """Pi แจ้งว่าเสร็จงานแล้ว"""
    try:
        if pond_id in pending_jobs:
            # ย้ายจาก pending ไป completed
            job = pending_jobs.pop(pond_id)
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()
            job["result"] = result
            
            completed_jobs[pond_id] = job
            
            print(f"✅ บ่อ {pond_id} เสร็จงานแล้ว: {result}")
            
            return {
                "success": True,
                "message": f"บันทึกการเสร็จงานของบ่อ {pond_id} เรียบร้อย"
            }
        else:
            raise HTTPException(status_code=404, detail=f"ไม่พบงานสำหรับบ่อ {pond_id}")
            
    except Exception as e:
        print(f"❌ Error ในการบันทึกงานเสร็จ: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.get("/status")
async def get_status():
    """ดูสถานะระบบ"""
    return {
        "pending_jobs": len(pending_jobs),
        "completed_jobs": len(completed_jobs),
        "pending_job_list": list(pending_jobs.keys()),
        "completed_job_list": list(completed_jobs.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check สำหรับ Railway"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# === MAIN ===
if __name__ == "__main__":
    import os
    
    # ใช้ port จาก environment variable หรือ default 8000
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 เริ่มต้น Shrimp Farm Cloud Controller...")
    print(f"📡 API จะรันที่: http://0.0.0.0:{port}")
    print(f"📖 ดู API docs ที่: http://0.0.0.0:{port}/docs")
    
    uvicorn.run(
        "cloud_app:app",
        host="0.0.0.0",
        port=port,
        reload=False  # ปิด reload ใน production
    )
