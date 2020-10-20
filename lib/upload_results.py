import glob
import os

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore

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
        print("Uploading " + json_file)
        df = pd.read_json(json_file)
        tmp = df.to_dict(orient='records')
        list(map(lambda x: coll_ref.add(x), tmp))

def upload_csv_data(script_path, coll_ref):
    list_of_files = glob.glob(script_path + "/../results/*.csv")
    for csv_file in list_of_files:
        print("Uploading " + csv_file)
        df = pd.read_csv(csv_file)
        tmp = df.to_dict(orient='records')
        list(map(lambda x: coll_ref.add(x), tmp))

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