from __future__ import print_function
import httplib2
import os

from apiclient import discovery, http 
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json

SCOPES = ['https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/drive']

CLIENT_SECRET_FILE = 'photocopier.json'
APPLICATION_NAME = 'Photocopier'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.google')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'photocopier.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    directories = service.files().list(q='mimeType = "application/vnd.google-apps.folder" '
                                         'and name = "Google Photos"').execute()

    for folder in directories.get('files', []):
        print (folder.get('name') + ' ' + folder.get('id'))

    # get list of files to download
    results = service.files().list(q="'1djzko5WHYWgMxRs5O1Bt1POyM6rfQK-ivU8ibYNpY-A' in parents "                                     
                                     "and createdTime > '2018-02-15T00:00:00.000Z' "
                                     "and not appProperties has { key = 'downloaded' and value = 'true'}"
                                     ,
                                   fields="files(id, name, appProperties, "
                                          "createdTime, imageMediaMetadata/time, description)").execute()

    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(item)
            download(service=service, file_id=item.get('id'), file_name=item.get('name'))
            mark_as_downloaded(service=service, file_id=item.get('id'))


def download(service=None, file_id=None, file_name='download.jpg'):
    request = service.files().get_media(fileId=file_id)

    with open(file_name, 'wb') as f:
        downloader = http.MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))


def mark_as_downloaded(service=None, file_id=None):
    props = {"appProperties": {"downloaded": True}}
    result = service.files().update(fileId=file_id, body=props).execute()

    print(result)


if __name__ == '__main__':
    main()

