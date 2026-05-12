
import os
import json
from supabase import create_client, Client
import requests
from datetime import timedelta

# Load environment variables as secrets
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")
SUPABASE_ORG_ID = os.getenv("SUPABASE_ORG_ID")
SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")
TENCENTCLOUD_SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID")
TENCENTCLOUD_SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY")
TENCENTCLOUD_REGION = os.getenv("TENCENTCLOUD_REGION")

# Deployment plan
DEPLOYMENT_PLAN = {
    "instance_type": "Medium",
    "secrets": SUPABASE_ACCESS_TOKEN,
    "region": "Global (global)",
    "project_name": "segmenta",
    "branch": "main",
    "environment": "dev",
    "database_password": "insert password here",
    "pat": "insert personal access token here"
}

def deploy_supabase():
    """
    Deploy Supabase resources.
    """
    # Authenticate with Supabase
    supabase_url = "https://supabase.io"
    supabase_key = SUPABASE_ACCESS_TOKEN
    supabase_secret = None
    supabase = create_client(supabase_url, supabase_key, supabase_secret)

    # Create a new project
    create_project = {
        "name": DEPLOYMENT_PLAN["project_name"],
        "org_id": SUPABASE_ORG_ID,
        "database_password": DEPLOYMENT_PLAN["database_password"]
    }

    response = supabase.project.create_project(create_project)
    project_id = response["data"]["id"]

    # Run migrations/config
    supabase.project.run_migrations(project_id)

    # Wait for the project to be healthy
    while True:
        status = supabase.project.get_status(project_id)
        if status["status"] == "healthy":
            break
        else:
            print("Project is not healthy. Retrying in 10 seconds...")
            time.sleep(10)

    # Print the result
    print(f"Supabase project {project_id} is deployed.")

def deploy_tencent():
    """
    Deploy Tencent resources.
    """
    # Authenticate with Tencent
    secret_id = TENCENTCLOUD_SECRET_ID
    secret_key = TENCENTCLOUD_SECRET_KEY
    region = TENCENTCLOUD_REGION

    # Create a CAM user
    cam_user_secret = requests.post(
        f"https://capi.tencentcloudapi.com/v1/index.php?Action=CreateRamUser&SecretId={secret_id}&SecretKey={secret_key}&Region={region}&UserGroup=",
        json={}
    )
    cam_user_id = cam_user_secret.json()["UserId"]

    # Grant CVM permissions to the CAM user
    request_params = {
        "SecretId": secret_id,
        "SecretKey": secret_key,
        "Region": region,
        "Action": "CreateSecurityGroup",
        "UserGroup": cam_user_id
    }
    requests.post(
        f"https://cvm.api.qcloud.com/v2/index.php?Action=RunInstances",
        json=request_params
    )

    # Wait for the instance to be created
    while True:
        response = requests.get(
            f"https://cvm.api.qcloud.com/v2/index.php?Action=DescribeInstances",
            params={"SecretId": secret_id, "SecretKey": secret_key, "Region": region}
        )
        if response.json()["TotalCount"] > 0:
            break
        else:
            print("Instance is not created. Retrying in 10 seconds...")
            time.sleep(10)

    # Print the result
    print("Tencent cloud resources are deployed.")

# Run deployment
if __name__ == "__main__":
    deploy_supabase()
    deploy_tencent()
