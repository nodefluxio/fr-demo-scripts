# @title #### Dashboard Backend Config
VANILLA_ADDRESS = "192.168.103.46" # @param {type:"string"}
VANILLA_PORT = "8008" # @param {type:"string"}
FE_ENDPOINT = "api/enrollment"

from io import BytesIO
import requests
from PIL import Image
import base64
import time 
import pandas as pd
from tqdm import tqdm

url = f"http://{VANILLA_ADDRESS}:{VANILLA_PORT}/{FE_ENDPOINT}"

def image2bin(image):
    img_byte_array = BytesIO()
    image.save(img_byte_array, format='JPEG')
    return img_byte_array.getvalue()


def dashboard_enroll(image, payload):
    files = {
        ('images',('test.jpeg',image2bin(image),'image/jpeg'))
    }

    response = requests.request("POST", url, data=payload, files=files)
    res = response.json() 

    img_thumb = None
    try:
        base64_image_string = res['enrollment']['faces'][0]['image_thumbnail']
        decoded_bytes = base64.b64decode(base64_image_string)
        image_stream = BytesIO(decoded_bytes)
        img_thumb = Image.open(image_stream)

        return {
            'face_id': str(res['enrollment']['face_id']),
            'name': res['enrollment']['name'],
            'status': res['enrollment']['status'],
            'success': True,
        }, img_thumb
    except Exception as error:
        return {
            'face_id': None,
            'name': None,
            'status': str(error),
            'success': False,
        }, None

def bulk_enroll_with_metadata(in_df):
    file_names = []
    face_ids = []
    names = []
    status = []
    successes = []
    img_thumbs = []

    count = len(in_df)
    success_count = 0
    failed_count = 0
    print(">>> Face Enrollment Started DATA_COUNT:", count)
    
    for _, row in tqdm(in_df.iterrows(), total=count):
        img = Image.open(row['file_name'])

        payload = {
            'name': row['name'],
            # 'face_id': row['face_id'] # Enable this if want to use Custom Face ID, instead randomly generated
            'identity_number': row['id_num'],
            'gender': row['gender'],
            'birth_date': row['birth_date'],
            'birth_place': row['birth_place'],
            'status': row['status'],
        }
        print(">>> Enrolling Face with PAYLOAD:", payload)

        res, img_thumb = dashboard_enroll(img, payload)
        file_names.append(row['file_name'])
        face_ids.append(res['face_id'])
        names.append(res['name'])
        status.append(res['status'])
        successes.append(res['success'])
        if img_thumb:
            img_thumbs.append((img_thumb, res['face_id']))

        if res['success']:
            success_count = success_count + 1
        else:
            failed_count = failed_count + 1

        time.sleep(0.1)
    
    print(">>> Face Enrollment Finished SUCCESS_COUNT:", success_count, "FAILED_COUNT:", failed_count)

    out_df = pd.DataFrame(data={
            'file_name': file_names,
            'face_id': face_ids,
            'name': names,
            'status': status,
            'success': successes
        })
    
    return out_df, img_thumbs

def main():
    df = pd.read_csv('bulk_inputs/face_data_with_metadata.csv')
    print(">>> Sucessfully Read CSV Input")
    bulk_enroll_with_metadata(df)

if __name__ == "__main__":
    main()

