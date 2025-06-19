from internals.awxlauncher import *
import yaml

# convert to configmap file in container
print(f"Loading api relationships from yamlkeyfile /usr/CHANGEME/apikeys.yml")
with open("/usr/CHANGEME/apikeys.yml") as yamlkeyfile:
  APIKEYS = yaml.full_load(yamlkeyfile)
apikeyrelationships=APIKEYS["apikeyrelationships"]
print(f"apikeyrelationships is {apikeyrelationships}")
#apikeyrelationships={'sme':['sme automation','sme-dev'],'itcc':['itcc automation'],'windows':['windows automation'],'network':['network automation'],'linux':['linux automation'],'storage':['storage automation'],'sapbasis':['sap basis automation'],'pha': ['pha automation'], 'abds': ['ab data streaming automation'], 'cloudpd': ['cloud platform development automation']}
def evaluateRulesValidityOnly(apikeytouse):
  if apikeytouse.startswith('CHANGEME'):
    return "OK"
  for keycheck in apikeyrelationships:
    if apikeytouse.startswith(keycheck.lower()):
      return "OK"
  return "API key is not valid."

def keyGetter(apikeytouse):
  print(f"Checking {apikeytouse}")
  maxdigits=4
  for beginning in apikeyrelationships:
    if apikeytouse.startswith(beginning):
      return beginning 
  if apikeytouse[maxdigits-1].isupper() or apikeytouse[maxdigits-1].isnumeric() or apikeytouse[maxdigits-1]=="_":
     print(f"key is too long {apikeytouse[maxdigits]}")
     maxdigits=maxdigits-1
  return apikeytouse[:maxdigits]

def evaluateRules(apikeytouse,jobname,jobtype):
  labels=getJobLabels(jobname)
  if apikeytouse.startswith('CHANGEME'):
    return "OK"
  if jobtype=="jobname":
    # ServiceNow can run any job with snow in its title
    if apikeytouse.startswith('servicenow'):
      if "snow" in jobname.lower():
        return "OK"
  # Begin checks for org-specific
    orgID=getJobOrgByName(jobname,"job_templates")
  if jobtype=="jobid":
    print(f"jobid called {jobname}")
    labels=getJobRunLabels(jobname)
    if apikeytouse.startswith('servicenow'):
      if "snow" in getJobNameByID(jobname).lower():
        return "OK"
    orgID=getJobOrgByName(jobname,"jobs")
  print(f"{jobname} has labels {labels}.")
  print(f"orgID is {orgID}")
  orgname=getOrgNameByID(orgID)
  print(f"Validating if job template named {jobname} is in AWX org {orgname}")
  print(f"orgname is {orgname}")
  for keycheck in apikeyrelationships:
    if apikeytouse.startswith(keycheck.lower()):
      print(f"orgname is {orgname}")
      if  orgname.lower() in apikeyrelationships[keycheck]:
        print(f"Found {orgname} in api keys! Sending OK")
        return "OK"
  # new check to allow jobs to be ran by labels
  print(f"Failed org check. Checking job's labels.")
  if "all" in labels:
    print(f"all found in labels {labels}, API key is allowed to run {jobname}")
    return "OK"
  for label in labels:
    if apikeytouse.lower().startswith(label.strip().lower()):
      print(f"API key was matched {label}")
      return "OK"
  print("No valid org or labels found for API key for this job. Giving up!")
  return "Cannot run a job that isn't in the AWX org the API key is tied to and has no labels tied to API key. Check if CHANGEMEpi_user has execute access to the job and if it has read access to the AWX org containing the job."

