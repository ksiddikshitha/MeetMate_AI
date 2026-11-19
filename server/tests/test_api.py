import os
os.environ['DATABASE_URL']='sqlite:///./test-meetmate.db'
os.environ['GROQ_API_KEY']=''
os.environ['DEMO_MODE']='true'
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health_and_status():
    assert client.get('/api/health').json()['status']=='ok'
    result=client.get('/api/config/status').json(); assert result['status']=='Demo Mode' and 'groq_api_key' not in result

def test_missing_key_is_unavailable_and_does_not_run_demo(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings,'demo_mode',False)
    monkeypatch.setattr(main.settings,'groq_api_key','')
    assert client.get('/api/config/status').json()['status']=='AI Unavailable'
    response=client.post('/api/meetings/analyze',json={'title':'No credentials','transcript':'A sufficiently long transcript for checking missing Groq credentials.'})
    assert response.status_code==503
    assert 'GROQ_API_KEY is missing' in response.json()['detail']
def test_demo_analysis_persists_and_export():
    r=client.post('/api/meetings/analyze',json={'title':'Planning','transcript':'Jordan will prepare the launch brief. The team decided to use the blue design.'})
    assert r.status_code==200, r.text
    meeting=r.json(); assert meeting['demo_mode'] is True and meeting['action_count']==1 and meeting['decision_count']==1
    assert meeting['open_clarification_count']>=1
    detail=client.get(f"/api/meetings/{meeting['id']}").json(); assert detail['transcript'].startswith('Jordan')
    assert client.get(f"/api/meetings/{meeting['id']}/export").status_code==200
    assert client.patch(f"/api/action-items/{detail['actions'][0]['id']}",json={'status':'Completed'}).json()['status']=='Completed'
    assert client.delete(f"/api/meetings/{meeting['id']}").json()['deleted'] is True
    assert client.get(f"/api/meetings/{meeting['id']}").status_code==404
def test_input_validation():
    assert client.post('/api/meetings/analyze',json={'title':'','transcript':'too short'}).status_code==422
    assert client.post('/api/meetings/analyze',json={'title':'Okay','transcript':'long enough transcript content'}).status_code==200
def test_clarification_answer():
    r=client.post('/api/meetings/analyze',json={'title':'Follow up','transcript':'The team should send the updated deck.'}).json()
    items=client.get('/api/clarifications?status=Open').json()
    c=next(x for x in items if x['meeting_id']==r['id'] and x['field']=='owner')
    ans=client.post(f"/api/clarifications/{c['id']}/answer",json={'response':'Jordan Lee'}).json()
    assert ans['resolved'] is True and ans['clarification']['status']=='Resolved'
    aid=ans['clarification']['action_item_id']; assert client.get('/api/action-items').status_code==200
    assert any(x['id']==aid and x['owner']=='Jordan Lee' for x in client.get('/api/action-items').json())

def test_missing_owner_and_deadline_stay_unassigned():
    response=client.post('/api/meetings/analyze',json={'title':'Loose commitment','transcript':'Someone should finish the report soon.'})
    assert response.status_code==200
    meeting=response.json()
    action=client.get('/api/action-items').json()
    item=next(x for x in action if x['meeting_id']==meeting['id'])
    assert item['owner'] is None
    assert item['deadline'] is None
    open_clarifications=[c for c in meeting['clarifications'] if c['status']=='Open']
    assert {c['field'] for c in open_clarifications}>={'owner','deadline'}

def test_live_analysis_accepts_mocked_structured_response(monkeypatch):
    import app.main as main
    import json
    monkeypatch.setattr(main.settings,'groq_api_key','test-only-key')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    payload={'summary':'The team chose the blue design. Jordan will send the final file.','discussion_points':['Design direction'],'decisions':[{'description':'Use the blue design','owner':None,'evidence':'We decided to use the blue design.'}],'action_items':[{'title':'Send the final file','description':'Jordan will send the final file.','owner':'Jordan','deadline':None,'priority':'Unknown','evidence':'Jordan will send the final file.'}],'clarifications':[{'action_item_index':0,'ambiguity':'No deadline was stated.','question':'What is the confirmed deadline?','field':'deadline','original_statement':'Jordan will send the final file.'}]}
    class FakeClient:
        def __init__(self,**kwargs): self.chat=self; self.completions=self; self.models=self
        def list(self):
            class Model: id='openai/gpt-oss-120b'
            class Result: data=[Model()]
            return Result()
        def create(self,**kwargs):
            class Message: content=json.dumps(payload)
            class Choice: message=Message()
            class Result: choices=[Choice()]
            return Result()
    monkeypatch.setattr(main,'OpenAI',FakeClient)
    response=client.post('/api/meetings/analyze',json={'title':'Mock AI meeting','transcript':'We decided to use the blue design. Jordan will send the final file.'})
    assert response.status_code==200, response.text
    meeting=response.json()
    assert meeting['demo_mode'] is False
    assert meeting['decisions'][0]['description']=='Use the blue design'
    assert meeting['actions'][0]['owner']=='Jordan'
    assert meeting['actions'][0]['deadline'] is None
    assert meeting['clarifications'][0]['field']=='deadline'

def test_malformed_ai_json_returns_gateway_error(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings,'groq_api_key','test-only-key')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    class FakeClient:
        def __init__(self,**kwargs): self.chat=self; self.completions=self; self.models=self
        def list(self):
            class Model: id='openai/gpt-oss-120b'
            class Result: data=[Model()]
            return Result()
        def create(self,**kwargs):
            class Message: content='not valid json'
            class Choice: message=Message()
            class Result: choices=[Choice()]
            return Result()
    monkeypatch.setattr(main,'OpenAI',FakeClient)
    response=client.post('/api/meetings/analyze',json={'title':'Bad output','transcript':'A sufficiently long transcript for testing malformed model output.'})
    assert response.status_code==502
    assert 'malformed structured data' in response.json()['detail']

def test_provider_failure_does_not_fall_back_to_demo(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings,'groq_api_key','test-only-key')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    class BrokenClient:
        def __init__(self,**kwargs): self.chat=self; self.completions=self; self.models=self
        def list(self):
            class Model: id='openai/gpt-oss-120b'
            class Result: data=[Model()]
            return Result()
        def create(self,**kwargs): raise RuntimeError('provider offline')
    monkeypatch.setattr(main,'OpenAI',BrokenClient)
    response=client.post('/api/meetings/analyze',json={'title':'Provider offline','transcript':'A sufficiently long transcript for testing provider failures.'})
    assert response.status_code==502
    assert response.json()['detail']=='Could not reach the configured AI provider. Please retry.'
    assert client.get('/api/config/status').json()['status']=='AI Connected'

def test_placeholder_api_key_is_unavailable_without_explicit_demo(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings,'groq_api_key','your_groq_api_key_here')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    assert client.get('/api/config/status').json()['status']=='AI Unavailable'

def test_invalid_api_key_does_not_fall_back_to_demo(monkeypatch):
    import app.main as main
    from openai import AuthenticationError
    monkeypatch.setattr(main.settings,'groq_api_key','invalid-test-key')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    class InvalidAuthenticationError(AuthenticationError):
        def __init__(self): Exception.__init__(self,'invalid')
    class InvalidKeyClient:
        def __init__(self,**kwargs): self.models=self
        def list(self): raise InvalidAuthenticationError()
    monkeypatch.setattr(main,'OpenAI',InvalidKeyClient)
    assert client.get('/api/config/status').json()['status']=='AI Unavailable'
    response=client.post('/api/meetings/analyze',json={'title':'Invalid credentials','transcript':'A sufficiently long transcript to check invalid credentials.'})
    assert response.status_code==502
    assert 'Groq rejected GROQ_API_KEY' in response.json()['detail']

def test_unavailable_configured_model_returns_clear_error(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings,'groq_api_key','test-only-key')
    monkeypatch.setattr(main.settings,'groq_model','unavailable-model')
    monkeypatch.setattr(main.settings,'demo_mode',False)
    class ModelListClient:
        def __init__(self,**kwargs): self.models=self
        def list(self):
            class Model: id='llama-3.3-70b-versatile'
            class Result: data=[Model()]
            return Result()
    monkeypatch.setattr(main,'OpenAI',ModelListClient)
    status=client.get('/api/config/status').json()
    assert status['status']=='AI Unavailable'
    assert 'not available to this Groq account' in status['message']
    response=client.post('/api/meetings/analyze',json={'title':'Unavailable model','transcript':'A sufficiently long transcript for checking model availability.'})
    assert response.status_code==503
    assert 'not available to this Groq account' in response.json()['detail']

def test_insufficient_clarification_answer_stays_open():
    response=client.post('/api/meetings/analyze',json={'title':'Needs precise deadline','transcript':'Jordan will prepare the rollout plan.'})
    meeting=response.json()
    clarification=next(c for c in meeting['clarifications'] if c['field']=='deadline')
    answer=client.post(f"/api/clarifications/{clarification['id']}/answer",json={'response':'sometime soon'})
    assert answer.status_code==200
    assert answer.json()['resolved'] is False
    assert answer.json()['clarification']['status']=='Open'
