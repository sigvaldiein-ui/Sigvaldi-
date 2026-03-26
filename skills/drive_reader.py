import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

class MimirVision:
    def __init__(self):
        self.creds_path = "/workspace/credentials/mimir-sa.json"
        self.folder_id = "1HlyB39_5S-P8819UvOon66vE19XN6_L0"
        self.creds = service_account.Credentials.from_service_account_file(self.creds_path)
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_pdfs(self):
        query = f"'{self.folder_id}' in parents and mimeType='application/pdf'"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def read_pdf(self, filename):
        # Bráðabirgðalausn: Skilar staðfestingu á að skjalið finnist
        return f"Innihald skjalsins {filename} er tilbúið til greiningar hjá Mími."
