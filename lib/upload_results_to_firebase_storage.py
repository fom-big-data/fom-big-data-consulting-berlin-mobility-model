import glob
import os

from firebase_admin import credentials, initialize_app, storage

file_size_limit_mb = 100


def load_private_key(script_path, firebase_private_key_file):
    cert_path = os.path.join(script_path, firebase_private_key_file)
    cred = credentials.Certificate(cert_path)
    return cred


def upload_data(script_path, bucket):
    list_of_files = glob.glob(script_path + "/../results/*.geojson")
    for geojson_file in list_of_files:

        file_size_mb = os.stat(geojson_file).st_size / 1024 / 1024
        file_name = os.path.basename(geojson_file)

        if file_size_mb > file_size_limit_mb:
            print("⚠️ File to large " + geojson_file + " (must be " + str(file_size_limit_mb) + "mb, but is " + str(
                round(file_size_mb)) + "MB)")
        else:
            print("✔️ Uploading " + geojson_file)
            blob = bucket.blob(file_name)
            blob.upload_from_filename(geojson_file)


#
# Main
#

# Set script path
script_path = os.path.dirname(__file__)

# Set project specific parameters
firebase_database_url = "https://berlin-mobility.firebaseio.com/"
firebase_private_key_file = "berlin-mobility-firebase-adminsdk-6wjn3-3c92dc67f7.json"
firebase_storage_url = "berlin-mobility.appspot.com"

# Load connection credentials
cred = load_private_key(script_path, firebase_private_key_file)

# Initialize application
initialize_app(cred, {'storageBucket': firebase_storage_url})

# Clean data
upload_data(script_path, storage.bucket())
