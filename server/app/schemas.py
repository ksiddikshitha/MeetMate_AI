from datetime import date
from pydantic import BaseModel, Field
from typing import Literal
class DecisionIn(BaseModel): description:str; owner:str|None=None; evidence:str|None=None; timestamp:str|None=None
class ActionIn(BaseModel): title:str; description:str=''; owner:str|None=None; deadline:date|None=None; priority:Literal['High','Medium','Low','Unknown']='Unknown'; evidence:str|None=None
class ClarificationIn(BaseModel): action_item_index:int|None=None; ambiguity:str; question:str; field:str; original_statement:str
class Analysis(BaseModel): summary:str; discussion_points:list[str]=[]; decisions:list[DecisionIn]=[]; action_items:list[ActionIn]=[]; clarifications:list[ClarificationIn]=[]
class AnalyzeRequest(BaseModel): title:str=Field(min_length=1,max_length=250); meeting_date:date|None=None; participants:str|None=None; transcript:str=Field(min_length=20)
class MeetingPatch(BaseModel): title:str|None=None; meeting_date:date|None=None; participants:str|None=None
class ActionPatch(BaseModel): title:str|None=None; description:str|None=None; owner:str|None=None; deadline:date|None=None; priority:Literal['High','Medium','Low','Unknown']|None=None; status:Literal['Pending','In Progress','Completed','Blocked']|None=None
class AnswerRequest(BaseModel): response:str=Field(min_length=2,max_length=2000)
