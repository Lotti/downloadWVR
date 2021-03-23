import requests
import json
import base64
import config
import ast
import os
import shutil

collection_source_id = config.VISUAL_RECOGNITION['source']['model']['id']
VisualRecognition_source_url = config.VISUAL_RECOGNITION['source']['url']
VisualRecognition_source_apikey = config.VISUAL_RECOGNITION['source']['apikey']
qs_version = '?version='+ config.VISUAL_RECOGNITION['version']

username = 'apikey'.encode('UTF8')
password_source = VisualRecognition_source_apikey.encode('UTF8')
auth_source = base64.b64encode(username + b":"+password_source)

VisualRecognition_source_headers = {
    'X-Watson-Technology-Preview': "2018-10-15",
    "Authorization": "Basic " + auth_source.decode()
    }


def list_collections(url,headers):
    endpoint = '/collections'

    response = requests.request("GET", url + endpoint + qs_version, headers=headers)
    # print(response.text)
    return response.text

def list_images(collection_id,url,headers):
    endpoint = '/collections/'+ collection_id + '/images'

    response = requests.get(url + endpoint + qs_version, headers=headers)
    #print(response.text)
    return response.text

def get_training(image_id,collection_id,url,headers):
    endpoint = '/collections/'+ collection_id + '/images/' + image_id

    response = requests.get(url + endpoint + qs_version, headers=headers)
    #print(response.text)
    return response.text

def download_image(image,collection_id,url,headers,folder):
    image_id = image['image_id']
    filename = image['source']['filename']
    endpoint = '/collections/'+ collection_id + '/images/' + image_id + '/jpeg'

    # create folder to save image locally
    if not os.path.exists(folder):
        os.makedirs(folder)
    new_file = folder + '/' + filename

    response = requests.get(url + endpoint + qs_version, headers=headers, stream=True)
    # print(response.text)
    # print(response)
    if response.status_code == 200:
        print('\ndownloading....')
        with open(new_file, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return new_file
    else:
        return ''

def upload_image(file,training,collection_id,url,headers):
    endpoint = '/collections/'+ collection_id + '/images'

    files = {"images_file": open('./'+file,"rb")}
    payload={'training_data':json.dumps(training) }
    
    response = requests.post(url + endpoint + qs_version, data=payload, files=files, headers=headers)
    print(response.text)
    # print(response.text)
    return

def delete_file(filepath):
    try:
        if os.path.isfile(filepath):
            os.unlink(filepath)
        elif os.path.isdir(filepath): shutil.rmtree(filepath)
    except Exception as e:
        print(e)

# MAIN APPLICATION

# download list of images and collect image ids
# GET /v4/collections/{collection_id}/images
print('\naccessing images list from source')
source_images_text = list_images(collection_source_id,VisualRecognition_source_url,VisualRecognition_source_headers)
# print(source_images_raw)
source_images_raw = ast.literal_eval(source_images_text)
source_images = source_images_raw['images']
print('---> there are ' + str(len(source_images)) + ' images on source')

# download training info (json structure containing the labels for each image)
# GET /v4/collections/{collection_id}/images/{image_id}
i = 1
for image in source_images:
    
    training_text = get_training(image['image_id'],collection_source_id,VisualRecognition_source_url,VisualRecognition_source_headers)
    training_raw = ast.literal_eval(training_text)
    training_data = training_raw['training_data']
    filename = training_raw['source']['filename']
    print('\naccessing training info of image ' + str(i) +': ' + filename + ' ' + image['image_id'])

    # create folder to save training data locally
    TRAINING_FOLDER = 'training_classifier_' + collection_source_id
    if not os.path.exists(TRAINING_FOLDER):
        os.makedirs(TRAINING_FOLDER)
    print('saving training data')
    subfolder = []
    try:
        for object_identified in training_data['objects']:
            if object_identified['object'] not in subfolder:
                subfolder.append(object_identified['object'])
    except:
        print('no training data')
        subfolder = ['no_data']
    if len(subfolder) > 1:
        subfolder = ['multiple_objects']

    if not os.path.exists(TRAINING_FOLDER + '/' + subfolder[0]):
        os.makedirs(TRAINING_FOLDER + '/' + subfolder[0]) # create subdirectory

    with open(TRAINING_FOLDER + '/' + subfolder[0] + '/'+ os.path.splitext(filename)[0] + '.json', 'w') as outfile:  
        json.dump(training_raw, outfile)
    print('--> training data saved successfully')

    # download image from source service, save it locally
    # /v4/collections/{collection_id}/images/{image_id}/jpeg
    image_path = download_image(training_raw,collection_source_id,VisualRecognition_source_url,VisualRecognition_source_headers,TRAINING_FOLDER + '/' + subfolder[0])
    if image_path != '':
        print('--> image downloaded locally')
        i += 1
