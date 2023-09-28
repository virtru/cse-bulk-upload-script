import os
import sys
import argparse
import json
import asyncio
import pathlib
from google.oauth2 import service_account
from googleapiclient.discovery import build
from cse_map_folder import map_folders  # Import from cse_map_folder.py
from cse_driver import CseDriver
from cse_encrypter import CseEncrypter
from cse_idp import CseIdp
from cse_util import *
from cse_wrapper import CseWrapper
from cse_upload_test import upload

def parse_arguments():
    parser = argparse.ArgumentParser(description='Encrypt and upload files to Google Drive')
    parser.add_argument('-driveId', required=True, help='Drive ID')
    parser.add_argument('-scanPath', required=True, help='Path to scan')
    parser.add_argument('-parentId', required=True, help='Parent ID')
    parser.add_argument('-googleCredentials', required=True, help='Credentials File')
    parser.add_argument('-clientSecret', required=True, help='Client Secret File')
    parser.add_argument('-delegatedUser', required=True, help='Delegated User')
    return parser.parse_args()

async def map_wrapper(scan_path, drive_id, parent_id, drive_service, folderMap, fileMap):
  await map_folders(scan_path, drive_id, parent_id, drive_service, folderMap, fileMap)

def main():
    args = parse_arguments()
    drive_id = args.driveId
    scan_path = args.scanPath
    parent_id = args.parentId
    creds_path = args.googleCredentials
    client_secret = args.clientSecret
    delegated_user = args.delegatedUser
    
    idp = CseIdp(client_secret)
    driver = CseDriver(creds_path)
    driver.set_delegated_user(delegated_user)
    
    folderMap, fileMap = {}, {}
    authn = idp.get_authn_token()

    if not os.path.exists(scan_path):
        print(f"Error: The specified scan path '{scan_path}' does not exist.")
        sys.exit(1)

    if not os.path.isfile(creds_path):
        print(f"Error: Credentials file not found at '{creds_path}'.")
        sys.exit(1)

    try:
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=['https://www.googleapis.com/auth/drive'])
        drive_service = build('drive', 'v3', credentials=creds)
        asyncio.run(map_wrapper(scan_path, drive_id, parent_id, drive_service, folderMap, fileMap))

        for key,value in fileMap.items():
          fileName = value['name']
          parentId = value['parentId']
          filePath = key
          
          upload(filePath, parentId, fileName, authn, driver)         
        
    except Exception as e:
        print(f"Error with bulk upload: {str(e)}")

if __name__ == "__main__":
    main()
