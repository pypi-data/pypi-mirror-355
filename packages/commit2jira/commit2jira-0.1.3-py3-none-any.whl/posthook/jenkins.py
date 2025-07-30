import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

def get_crumb():
    url = f"{os.getenv('JENKINS_URL')}/crumbIssuer/api/json"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(os.getenv('JENKINS_USER'), os.getenv('JENKINS_TOKEN'))
    )
    response.raise_for_status()
    crumb = response.json()
    return {crumb["crumbRequestField"]: crumb["crumb"]}
    
    
def trigger_build(job_name=None):
    job_name = job_name or os.getenv('JENKINS_JOB', 'default-job-name')

    crumb = get_crumb()
    url = f"{os.getenv('JENKINS_URL')}/job/{job_name}/build"

    response = requests.post(
        url,
        headers=crumb,
        auth=HTTPBasicAuth(os.getenv('JENKINS_USER'), os.getenv('JENKINS_TOKEN'))
    )

    response.raise_for_status()
    print(f"✅ Jenkins job '{job_name}' triggered.")
