import os
import hashlib
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- STILLINGAR SKV. SOP v4.0 ---
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = '/workspace/mimir_net/config/mimir-drive-key.json'

def get_drive_service():
    """Tengist Google Drive API. Styður bæði Personal og Shared Drives."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ VILLA: Lykillinn fannst ekki í {SERVICE_ACCOUNT_FILE}")
        return None
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def calculate_md5(file_path):
    """Reiknar MD5 fingrafar til að tryggja 100% gagnaheilleika."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sync_to_drive(local_path, folder_id):
    """
    Sendir skrá í Höllina (Drive), staðfestir MD5, og eyðir staðbundnum gögnum.
    Bætt við: supportsAllDrives=True til að styðja Enterprise/Shared möppur.
    """
    service = get_drive_service()
    if not service: return False

    file_name = os.path.basename(local_path)
    local_md5 = calculate_md5(local_path)
    
    print(f"📦 Samstilli við Höllina: {file_name}")

    # 1. Athuga hvort skrá sé þegar til (MD5 vörn)
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, md5Checksum)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])

        if files:
            drive_md5 = files[0].get('md5Checksum')
            if drive_md5 == local_md5:
                print(f"✅ Gögn þegar til staðar og MD5 samsvarar. Sleppi upphali.")
                burn_local_file(local_path)
                return True
    except Exception as e:
        print(f"⚠️ Athugun á tilvist skráar mistókst: {e}")

    # 2. Upphal (Ný skrá eða breytt)
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(local_path, resumable=True)
    
    try:
        uploaded_file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, md5Checksum',
            supportsAllDrives=True
        ).execute()
        
        if uploaded_file.get('md5Checksum') == local_md5:
            print(f"🚀 Upphal tókst! Drive ID: {uploaded_file.get('id')}")
            burn_local_file(local_path)
            return True
        else:
            print("❌ VILLA: MD5 staðfesting mistókst eftir flutning!")
            return False
            
    except Exception as e:
        print(f"❌ VILLA í upphali: {e}")
        return False

def burn_local_file(path):
    """Zero-Data Footprint: Eyðir gögnum örugglega með Linux 'shred'."""
    print(f"🔥 Burning trace: {path}")
    exit_code = os.system(f"shred -u -z {path}")
    if exit_code != 0:
        if os.path.exists(path):
            os.remove(path)
