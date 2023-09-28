Python Setup

# Sample steps to Bulk Upload a Directory to Google Drive using CSE

1. Create a Parent Folder in Google Drive and get its Folder ID from the URL. 

2. Get the Drive ID, Parent ID, Service Account Credentials File and Client Secret from GCP.

3. Run the following commands:
  ```
  python3 -m venv new-env
  source new-env/bin/activate
  pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
  pip3 install tink
  ```

3. Feed the parameters for the command as follows:
  ```
  python3 cse_bulk_upload.py
  -scanPath="path_to_folder_to_scan"
  -driveId="drive_id"
  -parentId="parent_id"
  -googleCredentials="path_to_credentials_json_file"
  -clientSecret="path_to_client_secret_file"
  -delegatedUser="delegated_user"
  ```

4. When prompted to authorize, navigate to the link and login to Google using the delegated user

5. When complete, check Drive to see if relevant files have been mapped.