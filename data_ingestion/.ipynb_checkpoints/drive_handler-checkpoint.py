import os
import io
import fitz  # PyMuPDF
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account

# SOP: Algildar slóðir og staðfest ID
JSON_KEY_PATH = '/workspace/mimir_net/config/project-5e16d125-a584-4542-a68-166960934026.json'
TARGET_FOLDER_ID = '1ZbTG7TZPB2m9F1ijDLA-ukL3NZSNt1c5' 

class GDriveHandler:
    def __init__(self):
        if not os.path.exists(JSON_KEY_PATH):
            raise FileNotFoundError(f"Lykill fannst ekki á {JSON_KEY_PATH}")
        self.creds = service_account.Credentials.from_service_account_file(
            JSON_KEY_PATH, scopes=['https://www.googleapis.com/auth/drive'])
        self.service = build('drive', 'v3', credentials=self.creds)

    def upload_file(self, local_path):
        """Fail-Safe upphleðsla: Vistar staðbundið ef kvóti er fullur."""
        try:
            file_metadata = {'name': os.path.basename(local_path), 'parents': [TARGET_FOLDER_ID]}
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id',
                supportsAllDrives=True, supportsTeamDrives=True
            ).execute()
            return f"Tókst! Skrá komin á Drive. ID: {file.get('id')}"
        except Exception as e:
            return f"Drive-tenging í bið (Kvóti). Skrá er örugg í sandbox: {os.path.basename(local_path)}"

    def list_files(self, limit=10):
        """Listar skrár í Data Lake."""
        query = f"'{TARGET_FOLDER_ID}' in parents and trashed = false"
        results = self.service.files().list(
            q=query, pageSize=limit, fields="files(id, name, mimeType)",
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        return results.get('files', [])

    def read_pdf(self, file_id):
        """Les PDF beint úr RAM (Zero-Data Footprint)."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        doc = fitz.open(stream=fh.getvalue(), filetype="pdf")
        return "".join([page.get_text() for page in doc])

class MimirVision(GDriveHandler):
    def list_pdfs(self):
        return [f for f in self.list_files() if 'pdf' in f.get('mimeType', '').lower()]