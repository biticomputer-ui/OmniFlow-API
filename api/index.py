from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import urllib.request
import json
import os

app = FastAPI(title="OmniFlow Brain API", version="1.0")

SECRET_DIRECTOR_PROMPT = """
Bạn là OmniFlash Creator Director. Hãy chuyển kịch bản sau thành các video prompt 9:16.
Tuân thủ 160 dòng lệnh Đạo diễn tuyệt mật của OmniFlash.

# OMNIFLASH CREATOR DIRECTOR — COMMUNITY CORE
Skill chuyển transcript thành từng prompt video OmniFlash 9:16. Giữ các hard-lock về lời thoại, runtime, kinetic text, đạo diễn, continuity và định dạng đầu ra.

## Nhịp độ và Phân đoạn (Workflow)
1. Xác định runtime trước khi chọn shot (4s, 6s, 8s, 10s).
2. Tốc độ nói tiếng Việt: 235-245 từ/phút. Không bao giờ ép tốc độ đọc để nhét vừa container.
3. Không bao giờ cắt gọt lời thoại (Giữ 100% transcript).
4. Kinetic Text: Hiển thị 3-5 từ một lúc, có hiệu ứng 3D pop-out, neon, metallic.
5. Luôn chèn B-roll, 3D Icon, và Âm thanh (SFX) dày đặc (Hyper-Creator Style).

## Đầu ra bắt buộc (Output Contract)
Trả về ĐÚNG định dạng sau, mỗi prompt nằm trong 1 code block:

SHOT 01 — 6s
```text
[Nội dung Prompt chi tiết cho Shot 01, bao gồm ngoại hình nhân vật (giữ nguyên không đổi), hành động, b-roll, hiệu ứng chữ, sfx]
```

SHOT 02 — 8s
```text
[Nội dung Prompt chi tiết cho Shot 02...]
```
"""

# Vercel sẽ tự động đọc biến môi trường này
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "NHAP_API_KEY_TRA_PHI_CUA_BAN_VAO_VERCEL")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Khởi tạo Supabase Client
from supabase import create_client, Client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class TranscriptRequest(BaseModel):
    transcript: str

def verify_license(authorization: str = Header(None)):
    if not authorization:
         raise HTTPException(status_code=401, detail="Thiếu License Key (Header Authorization)")
    
    key = authorization.replace("Bearer ", "")
    
    if not supabase:
         raise HTTPException(status_code=500, detail="Chưa cấu hình Supabase URL và Key trên Vercel!")
         
    # Truy vấn bảng 'licenses' trên Supabase
    try:
        response = supabase.table("licenses").select("*").eq("key", key).execute()
        data = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối cơ sở dữ liệu: {str(e)}")

    if not data:
        raise HTTPException(status_code=403, detail="License Key không tồn tại!")
        
    license_info = data[0]
    if license_info.get("status") != "active":
        raise HTTPException(status_code=403, detail="License Key đã bị khóa hoặc hết hạn!")
        
    return key

@app.get("/")
def read_root():
    return {"message": "OmniFlow Brain API đang chạy ngon lành trên Vercel!"}

@app.post("/v1/generate-shots")
async def generate_shots(req: TranscriptRequest, license_key: str = Depends(verify_license)):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GOOGLE_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": SECRET_DIRECTOR_PROMPT + "\n\nTranscript:\n" + req.transcript}]}]
    }
    
    req_http = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req_http) as response:
            result = json.loads(response.read().decode('utf-8'))
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            return {"status": "success", "shots": raw_text} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
