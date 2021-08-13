import io
import os
# noinspection PyPackageRequirements
from typing import List

from googleapiclient.http import MediaIoBaseDownload

from config import Config
from models import Participant, Workshop


def create_certificate(workshop: Workshop, participant: Participant) -> str:
    # Copy the slide
    response = Config.DRIVE.files().copy(fileId=Config.CERTIFICATE_FILE_ID).execute()
    file_id = response["id"]
    # Replace text
    request_body = {
        "requests": [
            {"replaceAllText": {"containsText": {"text": "{{name}}"}, "replaceText": participant.name}},
            {"replaceAllText": {"containsText": {"text": "{{title}}"}, "replaceText": workshop.title}},
            {"replaceAllText": {"containsText": {"text": "{{date}}"}, "replaceText": workshop.date_format}},
            {"replaceAllText": {"containsText": {"text": "{{topic}}"}, "replaceText": workshop.topic}},
            {"replaceAllText": {"containsText": {"text": "{{venue}}"}, "replaceText": workshop.venue}},
            {"replaceAllText": {"containsText": {"text": "{{instructor}}"}, "replaceText": workshop.instructor}},
        ]
    }
    Config.SLIDES.presentations().batchUpdate(presentationId=file_id, body=request_body).execute()
    # Download the file as pdf
    request = Config.DRIVE.files().export_media(fileId=file_id, mimeType="application/pdf")
    filename = f"{file_id}.pdf"
    file_path = os.path.join(Config.DOWNLOAD_PATH, filename)
    file_handle = io.FileIO(file_path, "w")
    downloader = MediaIoBaseDownload(file_handle, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()
    # Delete the copied slide from drive
    Config.DRIVE.files().delete(fileId=file_id).execute()
    # Upload pdf into google cloud storage
    blob = Config.CERTIFICATE_BUCKET.blob(filename)
    blob.upload_from_filename(file_path)
    # Delete pdf from local machine
    os.remove(file_path)
    return filename


def certificate_download(filename: str) -> str:
    file_path = os.path.join(Config.DOWNLOAD_PATH, filename)
    blob = Config.CERTIFICATE_BUCKET.blob(filename)
    blob.download_to_filename(file_path)
    return file_path


def certificate_delete(filename: str) -> str:
    if not filename:
        return "Certificate filename not specified"
    blob = Config.CERTIFICATE_BUCKET.blob(filename)
    if not blob.exists():
        return "Certificate NOT found"
    blob.delete()
    return str()


def batch_certificate_delete(workshop_id: str) -> None:
    participants: List[Participant] = Participant.objects.filter_by(workshop_id=workshop_id).get()
    filenames: List[str] = [participant.certificate_pdf for participant in participants if participant.certificate_pdf]
    for participant in participants:
        participant.certificate_pdf = str()
    Participant.save_all(participants)
    blobs = [Config.CERTIFICATE_BUCKET.blob(filename) for filename in filenames]
    blobs = [blob for blob in blobs if blob.exists()]
    for blob in blobs:
        blob.delete()
    return
