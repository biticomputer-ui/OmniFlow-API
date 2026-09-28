from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import urllib.request
import json
import os

app = FastAPI(title="OmniFlow Brain API", version="1.0")

SECRET_DIRECTOR_PROMPT = """
Bạn là OmniFlash Creator Director. Hãy chuyển kịch bản sau thành các video prompt 9:16.
Tuân thủ 160 dòng lệnh Đạo diễn tuyệt mật của OmniFlash.
(Để trống tượng trưng ở đây, bạn có thể copy nội dung từ file OmniFlash_Prompt_Skill.txt dán vào sau)
"""

# Vercel sẽ tự động đọc biến môi trường này nếu bạn set trên Vercel Dashboard
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "NHAP_API_KEY_TRA_PHI_CUA_BAN_VAO_VERCEL")

VALID_LICENSES = {
    "VIP_KEY_123": {"user": "Khách hàng A", "status": "active"},
    "TEST_KEY_456": {"user": "Khách hàng B", "status": "expired"}
}

class TranscriptRequest(BaseModel):
    transcript: str

def verify_license(authorization: str = Header(None)):
    if not authorization:
         raise HTTPException(status_code=401, detail="Thiếu License Key (Header Authorization)")
    key = authorization.replace("Bearer ", "")
    if key not in VALID_LICENSES or VALID_LICENSES[key]["status"] != "active":
        raise HTTPException(status_code=403, detail="License Key không hợp lệ hoặc đã hết hạn!")
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
