import glob
import json
import os

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore

file_size_limit_mb = 1


def load_private_key(script_path, firebase_private_key_file):
    cert_path = os.path.join(script_path, firebase_private_key_file)
    cred = credentials.Certificate(cert_path)
    return cred


def open_database_connection(cred, firebase_database_url, firebase_collection_name):
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_database_url})
    db = firestore.client()
    coll_ref = db.collection(firebase_collection_name)
    return coll_ref


def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print("Deleting doc " + doc.id)
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


def upload_json_data(script_path, coll_ref):
    list_of_files = glob.glob(script_path + "/../results/*.json")
    for json_file in list_of_files:
        file_size_mb = os.stat(json_file).st_size / 1024 / 1024
        file_name = os.path.basename(json_file)

        if file_size_mb > file_size_limit_mb:
            print("⚠️ File to large " + json_file + " (must be 10MB, but is " + str(round(file_size_mb)) + "MB)")
        else:
            with open(json_file) as file:
                print("✔️ Uploading " + json_file)
                data = json.load(file)
                coll_ref.document(file_name).set(document_data=data)


def upload_geojson_data(script_path, coll_ref):
    list_of_files = glob.glob(script_path + "/../results/*.geojson")
    for json_file in list_of_files:
        file_size_mb = os.stat(json_file).st_size / 1024 / 1024
        file_name = os.path.basename(json_file)

        if file_size_mb > file_size_limit_mb:
            print(
                "⚠️ File to large " + json_file + " (must be " + str(file_size_limit_mb) + "MB, but is " + str(round(file_size_mb)) + "MB)")
        else:
            with open(json_file) as file:
                print("✔️ Uploading " + json_file)
                data = json.load(file)
                coll_ref.document(file_name).set(document_data=data)


def upload_csv_data(script_path, coll_ref):
    list_of_files = glob.glob(script_path + "/../results/*.csv")
    for csv_file in list_of_files:
        file_size_mb = os.stat(csv_file).st_size / 1024 / 1024
        file_name = os.path.basename(csv_file)

        if file_size_mb > file_size_limit_mb:
            print(
                "⚠️ File to large " + csv_file + " (must be " + str(file_size_limit_mb) + "mb, but is " + str(round(file_size_mb)) + "MB)")
        else:
            print("✔️ Uploading " + csv_file)
            df = pd.read_csv(csv_file)
            tmp = df.to_dict(orient='records')
            list(map(lambda x: coll_ref.add(x, document_id=file_name), tmp))


#
# Main
#

# Set script path
script_path = os.path.dirname(__file__)

# Set project specific parameters
firebase_database_url = "https://berlin-mobility.firebaseio.com/"
firebase_private_key_file = "berlin-mobility-firebase-adminsdk-6wjn3-3c92dc67f7.json"
firebase_collection_name = "results"

# Load connection credentials
cred = load_private_key(script_path, firebase_private_key_file)

# Retrieve collection reference
coll_ref = open_database_connection(cred, firebase_database_url, firebase_collection_name)

# Clean data
delete_collection(coll_ref, 10_000)
upload_json_data(script_path, coll_ref)
upload_csv_data(script_path, coll_ref)
upload_geojson_data(script_path, coll_ref)
