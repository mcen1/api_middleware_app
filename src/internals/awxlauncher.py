#!/bin/env python3
import requests
import json
import time
import urllib3
import os
import datetime
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def lookupKey(keytofind):
  print(f"Looking up {keytofind} in environment variables...")
  if keytofind in os.environ:
    print(f"Found {keytofind} in environment variables!")
  else:
    print(f"Couldn't find {keytofind} in environment variables. A default value might be used.")
  return os.environ.get(str(keytofind))
token=''
awx_url=''
try:
  CONFIGMAP_DIR=lookupKey('CONFIGMAP_DIR')
except Exception as e:
  print(f'ERROR: CONFIGMAP_DIR undefined! Cannot control AWX job throttling. Error: {e}')

try:
  with open(f"{CONFIGMAP_DIR}/throttle.json", 'r') as file:
    THROTTLE_JOBS = json.load(file)
  print(f"THROTTLE_JOBS: {THROTTLE_JOBS}")
except FileNotFoundError:
    print(f"Error: The file {CONFIGMAP_DIR}/throttle.json was not found.")
except json.JSONDecodeError:
    print("Error: Could not decode JSON from the file. Check for valid JSON syntax.")

try:
  token=lookupKey('AWX_TOKEN')
except Exception as e:
  print(f'ERROR: AWX_TOKEN undefined! Cannot launch any AWX jobs. Error: {e}')
  token=''
if not token:
  print('ERROR: AWX_TOKEN undefined! Cannot launch any AWX jobs.')
  token=''
headers={"Content-type": "application/json", "Authorization":"Bearer "+token}
try:
  awxurl=lookupKey('AWX_URL')
except Exception as e:
  print('ERROR: AWX_URL undefined environment variable. Cannot launch any AWX jobs. Error: {e}')
  awxurl=''
if not awxurl:
  print('ERROR: AWX_URL is empty. Cannot launch any AWX jobs. {awxurl}')
try:
  maxruntime=int(lookupKey('MAX_RUNTIME'))
except:
  maxruntime=600
try:
  maxjobqueue=int(lookupKey('MAX_JOBQUEUE'))
except:
  # zero means no throttle for jobs not explicitly listed in THROTTLED_JOBS below
  maxjobqueue=0

try:
  debugMode=lookupKey('DEBUG_MODE')
except:
  debugMode=False

try:
  certVerify = lookupKey('CERT_VERIFY')
except Exception as e:
  certVerify = '/etc/ssl/certs/ca-certificates.crt'

if not certVerify:
  certVerify = '/etc/ssl/certs/ca-certificates.crt'

if certVerify.lower()=="false":
  certVerify=False

print(f"awxurl is {awxurl}\ncertVerify is {certVerify}\ndebugMode is {debugMode}\nmaxruntime is {maxruntime}")
finalstatuses=["successful","failed","cancelled","canceled","error"]
concerningstatuses=["failed","cancelled","cancelled","error"]

def getAWXHealth():
  try:
    url=f"https://{awxurl}/api/v2/config/"
    x = requests.get(url, verify=certVerify,headers=headers)
    job_output=json.loads(x.text)
    if 'time_zone' not in job_output:
      return "error Could not validate AWX connectivity"
  except Exception as e:
    print(f"exception: {e}")
  return "allgood"

print(f"awx health is {getAWXHealth()}")

def debugPrint(message):
  if debugMode:
    print(message)

def followJob(jobID):
  url=f"https://{awxurl}/api/v2/jobs/{jobID}"
  x = requests.get(url, verify=certVerify,headers=headers)
  json_output=json.loads(x.text)
  #print(json.dumps(json_output, indent=4))
  debugPrint(f"status: {json_output}")
  return json_output

def cancelJob(jobID):
  url=f"https://{awxurl}/api/v2/jobs/{jobID}/cancel/"
  x = requests.post(url,json={"id":jobID}, verify=certVerify,headers=headers)
  json_output=x.text
  #json_output=json.loads(x.text)
  #print(json.dumps(json_output, indent=4))
  debugPrint(f"status: {json_output} {x}")
  #print(f"{x.status_code}")
  return {"response": json_output, "status_code": x.status_code}


def getJobOutput(jobID):
  now = datetime.datetime.now()
  print(f"{now} Trying to retrieve output of job ID {jobID}.")
  url=f"https://{awxurl}/api/v2/jobs/{jobID}/stdout?format=txt"
  x = requests.get(url, verify=certVerify,headers=headers)
  job_output=x.text
  #print(json.dumps(json_output, indent=4))
  return job_output

def getJobOutputByFormat(jobID,outputformat):
  now = datetime.datetime.now()
  print(f"{now} Trying to retrieve output of job ID {jobID}.")
  url=f"https://{awxurl}/api/v2/jobs/{jobID}/stdout?format={outputformat}"
  x = requests.get(url, verify=certVerify,headers=headers)
  job_output=x.text
  #print(json.dumps(json_output, indent=4))
  return job_output

def templateResultFilter(fullresults):
  filtered = []
  for item in fullresults:
    started=item.get('started') or 'unknown'
    finished=item.get('finished') or 'unknown'
    status=item.get('status') or 'unknown'
    jobtype=item.get('type') or 'unknown'
    filtered_item = {
      'url': item['url'],
      'type': jobtype,
      'status': status,
      'id': item['id'],
      'started': started,
      'finished': finished,
      'organization': item['summary_fields']['organization']['name']
    }
    filtered.append(filtered_item)
  filtered.sort(key=lambda x: x['started'], reverse=True)
  return filtered

def getJobsByTemplateName(jobName):
  now = datetime.datetime.now()
  templateID=getJobIDByName(jobName)
  fullresults={"results":[]}
  print(f"{now} Trying to retrieve output of jobs associated to jobtemplate {jobName}.")
  # https://ap-dev.npd.CHANGEME.com/api/v2/job_templates/99/jobs/
  url=f"https://{awxurl}/api/v2/job_templates/{templateID}/jobs/?page_size=100"
  x = requests.get(url,verify=certVerify,headers=headers)
  json_output=json.loads(x.text)
  fullresults["results"].extend(json_output["results"])
  while str(json_output["next"]).lower()!="none":
    url=f"https://{awxurl}{json_output['next']}"
    x = requests.get(url,verify=certVerify,headers=headers)
    json_output=json.loads(x.text)
    fullresults["results"].extend(json_output["results"])
  filtered_results=templateResultFilter(fullresults['results'])
  return filtered_results 

def getJobOutputSanitized(jobID):
  job_stdout=getJobOutput(jobID)
  joboutput=followJob(jobID)
  returnstatus="unknown"
  try:
    returnstatus=joboutput["status"]
  except Exception as e:
    print(f"Error getting return_status in getJobOutputSanitized. Error: {e}")
  if returnstatus in concerningstatuses:
    extra_info=joboutput
  else:
    extra_info={}
  return {"job_status": returnstatus, "extra_info": extra_info,"job_stdout": job_stdout}




def trackJob(jobID,waittime,howmany,friendlyname):
  i=0
  returnstatus="unknown"
  starttime = int(time.time())
  extra_info = {}
  job_stdout = {}
  if int(waittime)<10:
    print(f"waittime of {waittime} is fewer than 10 seconds. Setting to 10 seconds...")
    waittime=10
  if (int(waittime) * int(howmany)) >maxruntime:
    print(f"Max wait time multiplied by loops is greater than {maxruntime} seconds. This API will stop checking status once {maxruntime} seconds have passed.")
  while i<howmany:
    time.sleep(waittime)
    now = datetime.datetime.now()
    joboutput=followJob(jobID)
    debugPrint(f"Loop: {i}")
    i=i+1
    returnstatus=joboutput["status"]
    print(f"{now} {friendlyname} job {jobID} status is {returnstatus}.")
    if returnstatus in finalstatuses:
      job_stdout=getJobOutput(jobID)
      if returnstatus in concerningstatuses:
        extra_info=joboutput
      else:
        extra_info={}
      break 
    if int(time.time())-starttime>=maxruntime:
      i=howmany
      now = datetime.datetime.now()
      extra_info=f"Maximum system-defined watch time of {maxruntime} seconds exceeded before job completed. Please use the job_status endpoint to continue tracking job ID {jobID}."
      print(extra_info)
  if i==howmany:
    if extra_info=={}:
      extra_info=f"Maximum job watch time exceeded before job completed. Looped {i} times with {waittime} seconds inbetween for a total of {i*waittime} seconds spent tracking job ID {jobID} for {friendlyname}. Job's final status is unknown. Please use the job_status endpoint to continue tracking this job."
      print(extra_info)
  return {"job_status": returnstatus, "extra_info": extra_info,"job_stdout": job_stdout, "job_id": jobID}

def launchNWaitJob(templateID,tosend):
  now = datetime.datetime.now()
  if str(templateID)=="False":
    return {"error": "Could not find templateID in org."}
  print(f"{now} Launching job with templateID of {templateID} to https://{awxurl}/api/v2/job_templates/{templateID}/launch/ with params of {tosend}...")
  url=f"https://{awxurl}/api/v2/job_templates/{templateID}/launch/"
  if "staging" in awxurl:
    print(f"We are using staging")
  if "dev" in awxurl:
    print(f"We are using dev")
  x = requests.post(url, json = tosend,verify=certVerify,headers=headers)
  print(f"Received response {x.text}")
  json_output=json.loads(x.text)
  if 'The requested resource could not be found.' in str(x.text):
    print(f"{now} Error launching job. Job was not found. Ensure job name was specified correctly and CHANGEMEPI user has 'execute' rights to job template in AWX.")
    return {"error": "Error launching job. Job was not found. Ensure job name was specified correctly and CHANGEMEPI user has 'execute' rights to job template in AWX."}
  try: 
    debugPrint(f"{now} Job ID is: {json_output['job']}")
  except Exception as e:
    print(f"{now} Error launching job: {e}. \n JSON was: {x.text}")
  try:
    toreturn=json_output['job']
  except:
    toreturn=json_output
  return toreturn


def awxPaginationFixer(baseurl,keytoget):
  fullresults={"results":[]}
  url=f"{baseurl}/?page_size=100"
  x = requests.get(url,verify=certVerify,headers=headers)
  json_output=json.loads(x.text)
  fullresults["results"].extend(json_output[keytoget])
  while str(json_output["next"]).lower()!="none":
    url=f"https://{awxurl}{json_output['next']}"
    print(f"url is {url}")
    x = requests.get(url,verify=certVerify,headers=headers)
    json_output=json.loads(x.text)
    fullresults["results"].extend(json_output["results"])
  return fullresults

def getJobOrgByName(jobname,apiendpoint):
  now = datetime.datetime.now()
  print(f"{now} Searching for job '{jobname}' in {apiendpoint}...")
  keyvalue="name"
  url=f"https://{awxurl}/api/v2/{apiendpoint}"
  keytoget="results"
  if apiendpoint=="jobs":
    keyvalue="id"
    keytoget="somethingelse"
    url=f"https://{awxurl}/api/v2/{apiendpoint}/{jobname}"
    x = requests.get(url,verify=certVerify,headers=headers)
    json_output=json.loads(x.text)
    print(f"getJobOrgByName getting from {url}")
    if "detail" in json_output and json_output["detail"]=="Not found.":
      return f"{jobname} not found"
    return json_output['organization']
  else:
    x = requests.get(url,verify=certVerify,headers=headers)
    json_output=json.loads(x.text)
    fullresults=awxPaginationFixer(url,keytoget)
    print(len(fullresults["results"]))
    if apiendpoint=="job_templates":
      for item in fullresults["results"]:
        print(f"checking item {item[keyvalue]}")
        if item[keyvalue].lower()==jobname:
          return item['organization']
  print(f"No org found. Job name: {jobname} API endpoint: {apiendpoint} Ensure CHANGEMEpi has execute access to job and read rights to AWX org")
  return f"no org found for {apiendpoint} please ensure CHANGEMEpi_user has execute access to job and read rights to AWX org"

# get labels from a job run as opposed to a job_template
def getJobRunLabels(jobid):
  now = datetime.datetime.now()
  print(f"{now} Searching for job '{jobid}' labels via getJobRunLabels...")
  keyvalue="name"
  url=f"https://{awxurl}/api/v2/jobs/{jobid}"
  keytoget="labels"
  x = requests.get(url,verify=certVerify,headers=headers)
  toreturn=[]
  try:
    json_output=json.loads(x.text)
    print(f"getting getJobRunLabels from {url}")
    labels=json_output['summary_fields']['labels']['results']
    for label in labels:
      if label['name'].lower().startswith('CHANGEMEpicanrun:'):
        toreturn.append(label['name'].split(':')[1].lower())
  except Exception as ex:
    print(f"Exception in getJobRunLabels: {ex}")
    toreturn=[]
  return toreturn

# get labels from a job_template
def getJobLabels(jobname):
  now = datetime.datetime.now()
  print(f"{now} Searching for job '{jobname}' labels...")
  keyvalue="name"
  jobID=getJobIDByName(jobname)
  url=f"https://{awxurl}/api/v2/job_templates/{jobID}"
  keytoget="labels"
  x = requests.get(url,verify=certVerify,headers=headers)
  toreturn=[]
  try:
    json_output=json.loads(x.text)
    print(f"getting getJobLabels from {url}")
    labels=json_output['summary_fields']['labels']['results']
    for label in labels:
      if label['name'].lower().startswith('CHANGEMEpicanrun:'):
        toreturn.append(label['name'].split(':')[1].lower())
  except Exception as ex:
    print(f"Exception from getJobLabels: {ex}")
    toreturn=[]
  return toreturn


def getJobNameByID(jobID):
  now = datetime.datetime.now()
  print(f"{now} getJobNameByID - Searching for job '{jobID}' in jobs...")
  url=f"https://{awxurl}/api/v2/jobs/{jobID}"
  x = requests.get(url,verify=certVerify,headers=headers)
  #print(f"getJobNameByID - {x.text}")
  json_output=json.loads(x.text)
  return json_output['name']


# testa
def getOrgNameByID(orgID):
  now = datetime.datetime.now()
  print(f"{now} Searching for org ID {orgID}...")
  url=f"https://{awxurl}/api/v2/organizations/{orgID}"
  x = requests.get(url,verify=certVerify,headers=headers)
  json_output=json.loads(x.text)
  #print(json_output)
  if 'name' in json_output:
    return json_output['name']
  return "organization not found"


def getJobIDByName(jobname):
  now = datetime.datetime.now()
  print(f"{now} getJobIDByName - Searching for job named {jobname}...")
  url=f"https://{awxurl}/api/v2/job_templates/"
  fullresults=awxPaginationFixer(url,"results")
  #print(fullresults["results"])
  for item in fullresults["results"]:
    if item["name"]==jobname:
      return item['id']
  return False

def getPendingJobsByID(jobID):
  now = datetime.datetime.now()
  print(f"{now} Retrieving pending jobs with template ID {jobID}...")
  url=f"https://{awxurl}/api/v2/job_templates/{jobID}/jobs/?status=pending"
  try:
    x = requests.get(url,verify=certVerify,headers=headers)
    json_output=json.loads(x.text)
    if 'results' in json_output and type(json_output['results'])==list:
      return json_output["results"]
  except Exception as ex:
    print(f"Exception in getPendingJobsByID: {ex}")
    if hasattr(x, 'text'):
      print(x.text)
    return []
  return []

def evaluateThrottle(jobname,jobID):
  # determine limit_pending for jobname
  throttled_found=next((job for job in THROTTLE_JOBS if job['job_name'] == jobname), None)
  if throttled_found:
    limit_pending=throttled_found['max_pending']
  else:
    limit_pending=maxjobqueue
  if limit_pending:
    # query awx for pending jobs
    pending=len(getPendingJobsByID(jobID))
    if pending >= limit_pending:
      return f'Denied by throttling rules due to {pending} {jobname} jobs already pending'
  return "OK"

if __name__ == "__main__":
   jobID=getJobIDByName("automation-awx-jobtesting-job")
   print(getJobLabels(jobID))
   quit()
   jobID=getJobIDByName("automation-awx-jobtesting-job")
   jobNumber=launchNWaitJob(jobID,{"extra_vars":{"from_xmatters":"greetings2"}})
   if not isinstance(jobNumber, int):
     print(jobNumber)
     quit()
   jobwait=5
   jobcycles=10
   print(trackJob(jobNumber,5,10,'automation-ansible-cacdemo-job'))
