import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import asyncio


folder_mime_type = 'application/vnd.google-apps.folder'

async def create_folder_in_drive(full_path, folder, parent_path, folder_map, drive_id, parent_id, drive_service):
    parent_folder = folder_map.get(parent_path)
    if parent_folder:
        parent_id = parent_folder['id']

    folder_metadata = {
        'name': folder,
        'mimeType': folder_mime_type,
        'driveId': drive_id,
        'parents': [parent_id],
    }

    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: drive_service.files().create(
            fields='id',
            supportsAllDrives=True,
            body=folder_metadata
        ).execute())
    except Exception as e:
        print(e)
        res = None

    if res:
        return res['id']

async def build_folder_and_file_map(dir_path, drive_id, parent_id, drive_service, folder_map=None, file_map=None):
    if folder_map is None:
        folder_map = {}
    if file_map is None:
        file_map = {}

    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        stats = os.stat(file_path)
        
        if os.path.isdir(file_path):
            folder_id = await create_folder_in_drive(  # Use await here
                file_path,
                file,
                dir_path,
                folder_map,
                drive_id,
                parent_id,
                drive_service
            )
            folder_map[file_path] = {'id': folder_id, 'name': file, 'parentId': parent_id}
            await build_folder_and_file_map(  # Use await here
                file_path,
                drive_id,
                folder_id,
                drive_service,
                folder_map,
                file_map
            )
        elif os.path.isfile(file_path):
          file_map[file_path] = {'name': file, 'parentId': parent_id}

    return {'folderMap': folder_map, 'fileMap': file_map}

def traverse_folder_map(folder_map):
    for folder_path, folder_info in folder_map.items():
        print('Folder Path:', folder_path)
        print('Folder Name:', folder_info['name'])
        print('Folder ID:', folder_info['id'])
        print('Parent ID:', folder_info['parentId'])
        print('---------------------------')

def traverse_file_map(file_map):
    for file_path, file_info in file_map.items():
        print('File Path:', file_path)
        print('File Name:', file_info['name'])
        print('Parent ID:', file_info['parentId'])
        print('---------------------------')

async def map_folders(scan_path, drive_id, parent_id, drive_service, folderMap, fileMap):
    try:
        folder_and_file_map = await build_folder_and_file_map(  # Use await here
            scan_path,
            drive_id,
            parent_id,
            drive_service,
            folderMap,
            fileMap
        )
        traverse_folder_map(folder_and_file_map['folderMap'])
        traverse_file_map(folder_and_file_map['fileMap'])
    except Exception as e:
        print(f'Error: {e}')
