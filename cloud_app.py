from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import json
import os

app = FastAPI(title="Shrimp Farm Cloud Controller", version="1.0.0")

# === CORS CONFIGURATION ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน production ควรระบุ domain ที่เฉพาะเจาะจง
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DATA MODELS ===
class LiftUpCommand(BaseModel):
    pondId: str  # frontend ส่งมาเป็น string
    action: str = "lift_up"
    timestamp: Optional[str] = None

class CamSideCommand(BaseModel):
    pondId: str  # frontend ส่งมาเป็น string
    action: str = "cam_side"
    timestamp: Optional[str] = None

class JobResponse(BaseModel):
    has_job: bool
    job_data: Optional[Dict[str, Any]] = None
    message: str

# === IN-MEMORY STORAGE ===
# ใน production ควรใช้ database แทน
pending_jobs: Dict[int, Dict[str, Any]] = {}
pending_job_RSPI2: Dict[int, Dict[str, Any]] = {}
completed_jobs: Dict[int, Dict[str, Any]] = {}

# === API ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "message": "Shrimp Farm Cloud Controller API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/lift-up": "ส่งคำสั่งยกยอขึ้น (Frontend)",
            "POST /api/cam-side": "ส่งคำสั่ง cam_side (Frontend)",
            "GET /job/{pond_id}": "Pi ถามว่ามีงานมั้ย (RSPI1)",
            "GET /job-rspi2/{pond_id}": "Pi ถามว่ามีงานมั้ย (RSPI2)",
            "POST /job/{pond_id}/complete": "Pi แจ้งงานเสร็จ (RSPI1)",
            "POST /job-rspi2/{pond_id}/complete": "Pi แจ้งงานเสร็จ (RSPI2)",
            "GET /status": "ดูสถานะระบบ"
        }
    }

@app.post("/api/cam-side")
async def create_cam_side_command(command: CamSideCommand):
    """Frontend ส่งคำสั่ง cam_side มา"""
    try:
        # แปลง pondId เป็น int
        pond_id = int(command.pondId)
        
        # เพิ่ม timestamp ถ้าไม่มี
        if not command.timestamp:
            command.timestamp = datetime.now().isoformat()
        
        # เก็บงานไว้ใน pending_job_RSPI2
        job_data = {
            "pond_id": pond_id,
            "action": command.action,
            "timestamp": command.timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        pending_job_RSPI2[pond_id] = job_data
        
        print(f"📝 รับคำสั่ง cam_side สำหรับบ่อ {pond_id} เรียบร้อย")
        
        return {
            "success": True,
            "message": f"คำสั่ง cam_side สำหรับบ่อ {pond_id} ถูกบันทึกแล้ว",
            "job_id": pond_id,
            "timestamp": command.timestamp
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="pondId ต้องเป็นตัวเลข")
    except Exception as e:
        print(f"❌ Error ในการรับคำสั่ง cam_side: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/api/lift-up")
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


@app.get("/job/{pond_id}")
async def get_job(pond_id: int):
    """Pi ถามว่ามีงานสำหรับบ่อนี้มั้ย (RSPI1)"""
    try:
        if pond_id in pending_jobs:
            job = pending_jobs[pond_id]
            print(f"📤 ส่งงานให้บ่อ {pond_id} (RSPI1): {job}")
            
            return JobResponse(
                has_job=True,
                job_data=job,
                message=f"มีงานสำหรับบ่อ {pond_id} (RSPI1)"
            )
        else:
            return JobResponse(
                has_job=False,
                job_data=None,
                message=f"ไม่มีงานสำหรับบ่อ {pond_id} (RSPI1)"
            )
            
    except Exception as e:
        print(f"❌ Error ในการตรวจสอบงาน RSPI1: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.get("/job-rspi2/{pond_id}")
async def get_job_rspi2(pond_id: int):
    """Pi ถามว่ามีงานสำหรับบ่อนี้มั้ย (RSPI2)"""
    try:
        if pond_id in pending_job_RSPI2:
            job = pending_job_RSPI2[pond_id]
            print(f"📤 ส่งงานให้บ่อ {pond_id} (RSPI2): {job}")
            
            return JobResponse(
                has_job=True,
                job_data=job,
                message=f"มีงานสำหรับบ่อ {pond_id} (RSPI2)"
            )
        else:
            return JobResponse(
                has_job=False,
                job_data=None,
                message=f"ไม่มีงานสำหรับบ่อ {pond_id} (RSPI2)"
            )
            
    except Exception as e:
        print(f"❌ Error ในการตรวจสอบงาน RSPI2: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/job/{pond_id}/complete")
async def complete_job(pond_id: int, result: Dict[str, Any]):
    """Pi แจ้งว่าเสร็จงานแล้ว (RSPI1)"""
    try:
        if pond_id in pending_jobs:
            # ย้ายจาก pending ไป completed
            job = pending_jobs.pop(pond_id)
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()
            job["result"] = result
            
            completed_jobs[pond_id] = job
            
            print(f"✅ บ่อ {pond_id} เสร็จงานแล้ว (RSPI1): {result}")
            
            return {
                "success": True,
                "message": f"บันทึกการเสร็จงานของบ่อ {pond_id} เรียบร้อย (RSPI1)"
            }
        else:
            raise HTTPException(status_code=404, detail=f"ไม่พบงานสำหรับบ่อ {pond_id} (RSPI1)")
            
    except Exception as e:
        print(f"❌ Error ในการบันทึกงานเสร็จ RSPI1: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.post("/job-rspi2/{pond_id}/complete")
async def complete_job_rspi2(pond_id: int, result: Dict[str, Any]):
    """Pi แจ้งว่าเสร็จงานแล้ว (RSPI2)"""
    try:
        if pond_id in pending_job_RSPI2:
            # ย้ายจาก pending_job_RSPI2 ไป completed
            job = pending_job_RSPI2.pop(pond_id)
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()
            job["result"] = result
            
            completed_jobs[pond_id] = job
            
            print(f"✅ บ่อ {pond_id} เสร็จงานแล้ว (RSPI2): {result}")
            
            return {
                "success": True,
                "message": f"บันทึกการเสร็จงานของบ่อ {pond_id} เรียบร้อย (RSPI2)"
            }
        else:
            raise HTTPException(status_code=404, detail=f"ไม่พบงานสำหรับบ่อ {pond_id} (RSPI2)")
            
    except Exception as e:
        print(f"❌ Error ในการบันทึกงานเสร็จ RSPI2: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@app.get("/status")
async def get_status():
    """ดูสถานะระบบ"""
    return {
        "pending_jobs": len(pending_jobs),
        "pending_job_RSPI2": len(pending_job_RSPI2),
        "completed_jobs": len(completed_jobs),
        "pending_job_list": list(pending_jobs.keys()),
        "pending_job_RSPI2_list": list(pending_job_RSPI2.keys()),
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
    
    # ใช้ port จาก environment variable หรือ default 3002
    port = int(os.environ.get("PORT", 3002))
    
    print("🚀 เริ่มต้น Shrimp Farm Cloud Controller...")
    print(f"📡 API จะรันที่: http://0.0.0.0:{port}")
    print(f"📖 ดู API docs ที่: http://0.0.0.0:{port}/docs")
    
    uvicorn.run(
        "cloud_app:app",
        host="0.0.0.0",
        port=port,
        reload=False  # ปิด reload ใน production
    )
