import os, tempfile
import httpx
os.environ['DATABASE_PATH'] = os.path.join(tempfile.gettempdir(), 'krishimitra-test.sqlite3')
from fastapi.testclient import TestClient
from app.main import app

def request(method, path, **kwargs):
    kwargs.setdefault('headers',{})
    kwargs['headers'].setdefault('X-Session-ID','11111111-1111-4111-8111-111111111111')
    with TestClient(app) as client:
        return getattr(client, method)(path, **kwargs)
def test_health():
    assert request('get','/api/health').json()['status']=='ok'
def test_chat_input_validation():
    assert request('post','/api/chat',json={'message':'x'}).status_code==422
def test_chat_context_validation():
    assert request('post','/api/chat',json={'message':'Can you advise?','context':{'field':'x'*121}}).status_code==422
def test_crop_validation():
    assert request('post','/api/crop-recommendations',json={'state':'X','district':'Y'}).status_code==422
def test_crop_recommendations():
    r=request('post','/api/crop-recommendations',json={'state':'Rajasthan','district':'Jaipur','soil_type':'Sandy','season':'Kharif','irrigation':'Rain-fed','land_area_acres':2,'budget':'Low','category':'Any'})
    assert r.status_code==200 and r.json()['recommendations']
def test_missing_ai_credentials_fallback(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    r=request('post','/api/chat',json={'message':'How can I save water?'})
    assert r.status_code==200 and r.json()['source']=='educational fallback'
def test_image_validation():
    r=request('post','/api/plant-health?crop=tomato&symptom=yellow%20leaves',files={'image':('bad.gif',b'GIF89a','image/gif')})
    assert r.status_code==415
def test_weather_failure(monkeypatch):
    async def fail(lat, lon): raise httpx.ConnectError('offline')
    monkeypatch.setattr('app.main.weather.forecast',fail)
    r=request('get','/api/weather?lat=10&lon=10')
    assert r.status_code==502 and 'temporarily unavailable' in r.json()['detail']
def test_chat_history():
    r=request('post','/api/chat',json={'message':'How can I save water?'})
    cid=r.json()['conversation_id']
    h=request('get',f'/api/chat-history/{cid}')
    assert h.status_code==200 and len(h.json()['messages'])==2
def test_chat_history_is_private_to_session():
    a='22222222-2222-4222-8222-222222222222'; b='33333333-3333-4333-8333-333333333333'
    with TestClient(app) as client:
        result=client.post('/api/chat',json={'message':'How can I save water?'},headers={'X-Session-ID':a}).json()
        assert client.get('/api/chat-history',headers={'X-Session-ID':b}).json()['conversations']==[]
        assert client.get(f"/api/chat-history/{result['conversation_id']}",headers={'X-Session-ID':b}).status_code==404
        assert client.delete(f"/api/chat-history/{result['conversation_id']}",headers={'X-Session-ID':b}).status_code==404
        assert client.get(f"/api/chat-history/{result['conversation_id']}",headers={'X-Session-ID':a}).status_code==200
