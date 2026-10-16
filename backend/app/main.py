import os, uuid, logging, time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from .database import init_db, connect
from .models.schemas import ChatRequest, CropRequest, FertilizerRequest, IrrigationRequest
from .services import weather, ai
from .services.agronomy import recommend

logging.basicConfig(level=logging.INFO)
@asynccontextmanager
async def lifespan(app):
    init_db(); yield
app=FastAPI(title='KrishiMitra API',version='1.0.0',lifespan=lifespan)
origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=['GET','POST','DELETE'],allow_headers=['*'])
_rate_buckets=defaultdict(deque)
def enforce_rate_limit(request: Request, limit=20, window=60):
    now=time.monotonic(); bucket=_rate_buckets[request.client.host if request.client else 'unknown']
    while bucket and bucket[0] <= now-window: bucket.popleft()
    if len(bucket)>=limit: raise HTTPException(429,'Too many requests. Please wait a minute and try again.')
    bucket.append(now)

@app.get('/api/health')
def health(): return {'status':'ok','ai_configured':bool(os.getenv('OPENAI_API_KEY'))}
@app.get('/api/geocode')
async def geocode(q: str=Query(min_length=2,max_length=100)):
    try: return {'results':await weather.geocode(q)}
    except (httpx.HTTPError,ValueError): raise HTTPException(502,'Location service is temporarily unavailable.')
@app.get('/api/weather')
async def get_weather(lat: float=Query(ge=-90,le=90),lon: float=Query(ge=-180,le=180)):
    try: return await weather.forecast(lat,lon)
    except httpx.HTTPError: raise HTTPException(502,'Weather service is temporarily unavailable. Please try again later.')
@app.post('/api/crop-recommendations')
def crop_recommendations(body: CropRequest): return recommend(body)
@app.post('/api/chat')
async def chat(body: ChatRequest, request: Request, session_id: str=Header(..., alias='X-Session-ID')):
    enforce_rate_limit(request)
    try: owner_id=str(uuid.UUID(session_id))
    except ValueError: raise HTTPException(400,'A valid browser session is required.')
    cid=body.conversation_id or str(uuid.uuid4())
    with connect() as db:
        existing=db.execute('SELECT owner_id FROM conversations WHERE id=?',(cid,)).fetchone()
        if body.conversation_id and (not existing or existing['owner_id']!=owner_id): raise HTTPException(404,'Conversation not found.')
        if not existing: db.execute('INSERT INTO conversations(id,owner_id) VALUES (?,?)',(cid,owner_id))
        rows=db.execute('SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 10',(cid,)).fetchall()
        history=[{'role':r['role'],'content':r['content']} for r in reversed(rows)]
        db.execute('INSERT INTO messages(conversation_id,role,content) VALUES (?,?,?)',(cid,'user',body.message))
    try: reply=await ai.answer(body.message,body.context,history)
    except (httpx.HTTPError,KeyError,ValueError): raise HTTPException(502,'The assistant is unavailable right now. Please retry or use the learning guides.')
    with connect() as db: db.execute('INSERT INTO messages(conversation_id,role,content) VALUES (?,?,?)',(cid,'assistant',reply))
    return {'conversation_id':cid,'reply':reply,'source':'configured AI' if os.getenv('OPENAI_API_KEY') else 'educational fallback'}
@app.get('/api/chat-history')
def history(session_id: str=Header(..., alias='X-Session-ID')):
    try: owner_id=str(uuid.UUID(session_id))
    except ValueError: raise HTTPException(400,'A valid browser session is required.')
    with connect() as db:
        rows=db.execute('SELECT c.id,c.created_at,COUNT(m.id) AS messages FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id WHERE c.owner_id=? GROUP BY c.id ORDER BY c.created_at DESC LIMIT 50',(owner_id,)).fetchall()
    return {'conversations':[dict(r) for r in rows]}
@app.get('/api/chat-history/{conversation_id}')
def conversation(conversation_id: str,session_id: str=Header(..., alias='X-Session-ID')):
    try: owner_id=str(uuid.UUID(session_id))
    except ValueError: raise HTTPException(400,'A valid browser session is required.')
    with connect() as db:
        allowed=db.execute('SELECT 1 FROM conversations WHERE id=? AND owner_id=?',(conversation_id,owner_id)).fetchone()
        if not allowed: raise HTTPException(404,'Conversation not found.')
        rows=db.execute('SELECT role,content,created_at FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id,)).fetchall()
    return {'conversation_id':conversation_id,'messages':[dict(r) for r in rows]}
@app.delete('/api/chat-history/{conversation_id}')
def delete_conversation(conversation_id: str,session_id: str=Header(..., alias='X-Session-ID')):
    try: owner_id=str(uuid.UUID(session_id))
    except ValueError: raise HTTPException(400,'A valid browser session is required.')
    with connect() as db:
        allowed=db.execute('SELECT 1 FROM conversations WHERE id=? AND owner_id=?',(conversation_id,owner_id)).fetchone()
        if not allowed: raise HTTPException(404,'Conversation not found.')
        db.execute('DELETE FROM messages WHERE conversation_id=?',(conversation_id,)); db.execute('DELETE FROM conversations WHERE id=? AND owner_id=?',(conversation_id,owner_id))
    return {'deleted':True}
@app.post('/api/fertilizer-guidance')
def fertilizer(body: FertilizerRequest):
    return {'label':'General educational information','crop':body.crop,'stage':body.stage,'guidance':['Base nutrient decisions on a current soil test and locally validated crop guidance.','Nitrogen supports leafy growth; phosphorus supports roots and energy transfer; potassium supports water regulation and plant resilience.','Organic matter from mature compost can improve soil structure; nutrient content varies.','Avoid applying fertilizer before heavy rain or directly into waterways. Follow the product label and local safety guidance.'],'recommendation':'No quantities are provided. Ask your soil testing laboratory or local agriculture extension officer for field-specific rates.'}
@app.post('/api/irrigation-guidance')
def irrigation(body: IrrigationRequest):
    return {'label':'Field-check guidance; no fixed schedule','guidance':[f'For {body.crop} at {body.stage}, check root-zone soil moisture before irrigating. Soil texture changes how quickly water drains and remains available.',f'Consider the reported rainfall ({body.rainfall}) and weather ({body.weather}); forecasts are uncertain and field conditions vary.','Drip can target the root zone, sprinklers distribute water over a crop, and surface methods need careful flow control to limit runoff.','Avoid irrigation when soil is already saturated; inspect for ponding and drainage problems.'],'assumptions':'No coordinates, soil moisture measurement, crop coefficient, or validated local calculation method was supplied, so no quantity or schedule is calculated.'}
@app.post('/api/plant-health')
async def plant_health(request: Request, crop: str=Query(min_length=2,max_length=80), symptom: str=Query(min_length=3,max_length=500), part: str=Query(default='leaves',max_length=50), duration: str=Query(default='',max_length=80), recent_weather: str=Query(default='',max_length=120), image: UploadFile|None=File(default=None)):
    enforce_rate_limit(request)
    if image:
        if image.content_type not in ('image/jpeg','image/png','image/webp'): raise HTTPException(415,'Upload a JPG, PNG, or WebP image.')
        data=await image.read(5*1024*1024+1)
        if len(data)>5*1024*1024: raise HTTPException(413,'Image must be 5 MB or smaller.')
        if not (data.startswith((b'\xff\xd8\xff',b'\x89PNG\r\n\x1a\n')) or (data.startswith(b'RIFF') and data[8:12]==b'WEBP')): raise HTTPException(415,'The uploaded file does not appear to be a supported image.')
    return {'label':'Preliminary symptom guidance, not a diagnosis','crop':crop,'part':part,'symptom':symptom,'reported_context':{'duration':duration,'recent_weather':recent_weather},'possible_causes':[{'cause':'Water stress or nutrient imbalance','why':'Can cause visible leaf changes; symptoms overlap across causes.'},{'cause':'Pest or disease pressure','why':'Needs inspection of both leaf surfaces, stems, and nearby plants.'}],'next_observations':['Check whether symptoms affect old or new leaves and whether they are spreading.','Look for insects, webbing, lesions, or patterns across neighboring plants.','Note recent irrigation, rainfall, fertilizer, and spray history.'],'low_risk_steps':['Avoid sudden fertilizer or pesticide applications until the cause is clearer.','Remove severely affected debris where practical and keep tools clean.','Consult a local agriculture extension officer or plant pathology expert if symptoms spread or plants decline.'],'vision':'Image stored or analyzed by no external model; questionnaire fallback used.'}
@app.get('/api/knowledge')
def knowledge():
    return {'articles':[{'topic':'Soil health','title':'Start with soil testing','summary':'A soil test helps guide balanced nutrient management. Use a recognized local laboratory and follow its interpretation.'},{'topic':'Water conservation','title':'Check soil before irrigating','summary':'Observe moisture in the active root zone and account for recent rain to reduce avoidable water use.'},{'topic':'Integrated pest management','title':'Monitor before treatment','summary':'Identify the pest, conserve beneficial organisms, and seek locally validated advice before treatment.'},{'topic':'Crop rotation','title':'Rotate crops where practical','summary':'Crop rotation can diversify production and help break some pest and disease cycles; choose locally suitable sequences.'},{'topic':'Composting','title':'Use mature compost thoughtfully','summary':'Composting crop residues and suitable organic materials can support soil structure. Compost nutrient content varies.'},{'topic':'Sowing and harvesting','title':'Follow the local crop calendar','summary':'Sowing and harvest timing depends on local climate, variety, and water. Ask your district agriculture office for current guidance.'},{'topic':'Fertilizer management','title':'Balance nutrients with a soil test','summary':'Use soil-test results to avoid guesswork and follow validated crop guidance and product labels.'},{'topic':'Post-harvest storage','title':'Keep grain dry and clean','summary':'Dry and store produce according to crop-specific local guidance; inspect stores for moisture and pests.'},{'topic':'Precision farming','title':'Use sensors as decision support','summary':'Field sensors and digital tools can help observe variability, but calibrate devices and compare readings with field checks.'},{'topic':'Sustainable agriculture','title':'Protect soil and beneficial life','summary':'Maintain ground cover where practical, reduce avoidable disturbance, and use integrated pest management.'}],'schemes':[],'schemes_note':'No scheme details are included without current official verification. Check your state agriculture department and official Government of India portals.'}

@app.exception_handler(Exception)
async def safe_error(request, exc):
    logging.exception('Unhandled API error')
    return JSONResponse(status_code=500,content={'detail':'An unexpected server error occurred.'})
