from fastapi import APIRouter, Request, status, Header
from fastapi.responses import JSONResponse
from internals.process_request import ProcessRequest
from internals.awxlauncher import *
from internals.apirules import *
from pydantic import BaseModel
import json
class AWXJobLaunchWait(BaseModel):
  job_name: str
  job_params: dict = {}
  job_waittime: int = 5
  job_cycles: int = 15

class AWXJobStatus(BaseModel):
  job_id: int
  output_format: str = ""

class AWXJobTemplate(BaseModel):
  job_name: str

router = APIRouter()

@router.post("/launch_n_wait", status_code=200, tags=[f"Automation - Launch AWX Job and Wait for Response"])
def launchAWXAndWait(awxjobinfo:AWXJobLaunchWait,req: Request,apikey: str = ''):
  endpoint = f"launch_n_wait"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_name.lower(),"jobname")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobID=getJobIDByName(awxjobinfo.job_name)
  keyused=keyGetter(apikeytouse)
  if "extra_vars" not in awxjobinfo.job_params:
    awxjobinfo.job_params["extra_vars"]={}
  awxjobinfo.job_params["extra_vars"]["_ab_CHANGEME_CHANGEMEpi_key"]=keyused
  awxjobinfo.job_params["extra_vars"]["_ab_CHANGEME_caller_supplied_extra_vars_keys"]=list(awxjobinfo.job_params["extra_vars"].keys())
  results=evaluateThrottle(awxjobinfo.job_name.lower(),jobID)
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={"errors": f"{results}"}
    )

  jobNumber=launchNWaitJob(jobID,awxjobinfo.job_params)
  if not isinstance(jobNumber, int):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": jobNumber}
    )
  jobwait=int(awxjobinfo.job_waittime)
  jobcycles=int(awxjobinfo.job_cycles)
  tosay=trackJob(jobNumber,jobwait,jobcycles,awxjobinfo.job_name)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": tosay}
  )
@router.post("/launch_nowait", status_code=200, tags=[f"Automation - Launch AWX Job without Waiting for Response"])
def launchAWXWithoutWait(awxjobinfo:AWXJobLaunchWait,req: Request,apikey: str = ''):
  endpoint = f"launch_no_wait"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_name.lower(),"jobname")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobID=getJobIDByName(awxjobinfo.job_name)
  keyused=keyGetter(apikeytouse)
  if "extra_vars" not in awxjobinfo.job_params:
    awxjobinfo.job_params["extra_vars"]={}
  awxjobinfo.job_params["extra_vars"]["_ab_CHANGEME_CHANGEMEpi_key"]=keyused
  awxjobinfo.job_params["extra_vars"]["_ab_CHANGEME_caller_supplied_extra_vars_keys"]=list(awxjobinfo.job_params["extra_vars"].keys())
  results=evaluateThrottle(awxjobinfo.job_name.lower(),jobID)
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={"errors": f"{results}"}
    )
  jobNumber=launchNWaitJob(jobID,awxjobinfo.job_params)
  if not isinstance(jobNumber, int):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": jobNumber}
    )
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobNumber}
  )

@router.post("/job_status", status_code=200, tags=[f"Automation - Get AWX Job Status"])
def launchAWXWithoutWait(awxjobinfo:AWXJobStatus,req: Request,apikey: str = ''):
  endpoint = f"job_status"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_id,"jobid")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobResults=getJobOutputSanitized(awxjobinfo.job_id)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )


@router.post("/job_status_format", status_code=200, tags=[f"Automation - Get AWX Job Status with Formatting"])
def jobStatusFormat(awxjobinfo:AWXJobStatus,req: Request,apikey: str = ''):
  endpoint = f"job_status_format"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_id,"jobid")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobResults=getJobOutputByFormat(awxjobinfo.job_id,awxjobinfo.output_format)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )

# followJob

@router.post("/job_info", status_code=200, tags=[f"Automation - Get AWX Job Info"])
def jobStatusFormat(awxjobinfo:AWXJobStatus,req: Request,apikey: str = ''):
  endpoint = f"job_info"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_id,"jobid")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobResults=followJob(awxjobinfo.job_id)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )

# getJobsByTemplateName
@router.post("/template_jobs", status_code=200, tags=[f"Automation - Get AWX Job IDs by template"])
def jobTemplateJobs(awxjobinfo:AWXJobTemplate,req: Request,apikey: str = ''):
  endpoint = f"template_jobs"
  apikeytouse=apikey
  print(f"Received {awxjobinfo}")
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  if not apikeytouse.startswith('CHANGEME'):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"Unavailable for this API key."}
    )
  jobResults=getJobsByTemplateName(str(awxjobinfo.job_name))
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )

@router.post("/cancel_job", status_code=200, tags=[f"Automation - Cancel AWX Job"])
def jobCanceller(awxjobinfo:AWXJobStatus,req: Request,apikey: str = ''):
  endpoint = f"cancel_job"
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_id,"jobid")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobResults=cancelJob(awxjobinfo.job_id)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )

@router.post("/get_concurrent_runs", status_code=200, tags=[f"Automation - Get concurrent AWX Job"])
def jobConcurrentRetriever(awxjobinfo:AWXJobTemplate,req: Request,apikey: str = ''):
  endpoint = f"get_concurrent_runs"
  print(f"awxjobinfo is {awxjobinfo}")
  apikeytouse=apikey
  if req.headers.get('apikey'):
    apikeytouse=req.headers.get('apikey')
  results=evaluateRules(apikeytouse,awxjobinfo.job_name,"jobname")
  if results!="OK":
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": f"{results}"}
    )
  jobID=getJobIDByName(awxjobinfo.job_name)
  jobResults=getPendingJobsByID(jobID)
  return JSONResponse(
  status_code=status.HTTP_200_OK,
  content={"results": jobResults}
  )
