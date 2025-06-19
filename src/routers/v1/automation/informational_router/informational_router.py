from fastapi import APIRouter, Request, status, Header
from fastapi.responses import JSONResponse
from internals.process_request import ProcessRequest
from internals.apirules import *
from internals.getsnow import *
from internals.getsectigo import *
from pydantic import BaseModel
import json
import time
from datetime import datetime

class SNOWThing(BaseModel):
  item_id: str = ""

class SectigoReq(BaseModel):
  cn: str = ""
  download_type: str = "pemia"
  customer: str = "Amerisource"

class PauseTimerCount(BaseModel):
  pause_time: str = "60"


router = APIRouter()

@router.post("/snow_item_info", status_code=200, tags=[f"Informational - Get information from a Service Now item (change, request, etc)"])
def retrieveInfoFromSNOWAPI(snowthing:SNOWThing,req: Request,apikey: str = ''):
  endpoint = f"snow_item_info"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRulesValidityOnly(apikeytouse)
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  print(f"retrieveInfoFromSNOWAPI called. snowthing is {snowthing}")
  snowResults=getSNOWItem(snowthing.item_id)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": snowResults}
  )

@router.post("/get_sectigo_current_signed_cert", status_code=200, tags=[f"Informational - Get base64 encoded cert"])
def retrieveInfoFromSectigoAPI(sectigoreq:SectigoReq,req: Request,apikey: str = ''):
  endpoint = f"get_sectigo_current_signed_cert"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRulesValidityOnly(apikeytouse)
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  sectigoResults=getSectigoCert(sectigoreq.cn,sectigoreq.customer,sectigoreq.download_type)
  print(f"sectigoResults is {sectigoResults}")
  if "errors" in sectigoResults:
    return JSONResponse(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    content={"results": sectigoResults}
    )
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": sectigoResults}
  )

@router.post("/timeouttest", status_code=200, tags=[f"Informational - Take time to respond to test timeout"])
def takeAWhileToReply(pausetimercount:PauseTimerCount):
  now = datetime.now()
  timetosleep=int(pausetimercount.pause_time)
  print(f"{now} Sleep called. Wait {timetosleep} seconds...")
  time.sleep(timetosleep)
  print(f"{now} Sleep is over. Sending response...")
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": f"Greetings. I slept for {timetosleep} seconds and issued this reply."}
  )

@router.get("/health", status_code=200, tags=[f"Get health"])
def getHealth():
  awxhealth=getAWXHealth()
  sectigohealth=getSectigoHealth()
  status="unhealthy"
  if awxhealth=="allgood" and sectigohealth=="allgood":
    status="allserviceshealthy"
  return JSONResponse(
  content={"allservices": status, "awx": awxhealth, "sectigo": sectigohealth}
  )
