import os
import io
import fitz  # PyMuPDF
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# ==========================================
# ⚙️ STILLINGAR - Mímir Vision v2.8
# ==========================================
JSON_KEY_PATH = '/workspace/credentials/mimir-sa.json'
TARGET_FOLDER_ID = '0AMDsY618eKP8Uk9PVA'

class MimirReader:
    def __init__(self):
        if not os.path.exists(JSON_KEY_PATH):
            raise FileNotFoundError(f"Lykill fannst ekki á {JSON_KEY_PATH}")
        
        # Auðkenning með Drive scopes
        self.creds = service_account.Credentials.from_service_account_file(
            JSON_KEY_PATH, scopes=['https://www.googleapis.com/auth/drive'])
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files(self, limit=10):
        """Finnur nýjustu skjölin í 30 TB Hallinni."""
        query = f"'{TARGET_FOLDER_ID}' in parents and trashed = false"
        results = self.service.files().list(
            q=query, pageSize=limit, fields="files(id, name, mimeType)").execute()
        return results.get('files', [])

    def read_pdf(self, file_id):
        """Sækir PDF og breytir í texta í RAM (Zero-Data Footprint)."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Opna PDF úr minni án þess að vista á disk (shred-vörn)
        doc = fitz.open(stream=fh.getvalue(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text

if __name__ == '__main__':
    try:
        reader = MimirReader()
        files = reader.list_files()
        
        print(f"\n🔎 Mímir rýnir í 30 TB Höllina...")
        
        if not files:
            print("📭 Hallin virðist tóm. Hentu PDF skjali í 'Mimir_Data_Lake' í vafranum!")
        else:
            for f in files:
                print(f" - Fann: {f['name']} [{f['mimeType']}]")
                if 'pdf' in f['mimeType'].lower():
                    print(f" 📖 Les PDF innihald beint úr RAM...")
                    content = reader.read_pdf(f['id'])
                    # Sýna fyrstu 200 stafina sem útdrátt
                    snippet = content[:200].replace('\n', ' ')
                    print(f" ✅ Útdráttur:\n{'-'*40}\n{snippet}...\n{'-'*40}")
    except Exception as e:
        print(f"❌ Villa í Drive Reader: {e}")