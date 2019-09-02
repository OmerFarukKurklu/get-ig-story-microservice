import requests
import json
import urllib.request
import falcon
import boto3
import os
import shutil
import time
from multiprocessing import Process

BUCKET_NAME = [BUCKET_NAME] #CHANGE THIS
USERNAME = [BOT_ACCOUNT_USERNAME] #CHANGE THIS
PASSWORD = [BOT_ACCOUNT_PASSWORD] #CHANGE THIS

def get_account_id(key):
    try:
        index = [x.isdigit() for x in key].index(True)
        username = key[:index]
        account_url = 'https://www.instagram.com/' + username + '/?__a=1'
        session = requests.Session()
        account_response = session.get(account_url).json()
        if account_response['graphql']['user']['is_private']:
            raise PermissionError()
        else:
            return account_response['graphql']['user']['id']
    except ValueError:
        log_update(key, '401 User does not exist', 'There are no user with username: '+ username)
    except PermissionError:
        log_update(key, '425 Private account', 'Account with username: '+ username +' is private')
    except Exception as e:
        log_update(key, '501 get_account_id FAILURE.', str(e))

def get_reels_media(account_id, key):
    BASE_URL = 'https://www.instagram.com/'
    LOGIN_URL = BASE_URL+ 'accounts/login/ajax/'
    USER_AGENT = 'Mozilla/5.0'
    media_url = 'https://www.instagram.com/graphql/query/?query_id=17873473675158481&variables={"reel_ids":["'+ account_id +'"], "precomposed_overlay":false}'
    try:
        session = requests.Session()
        session.headers = {'user-agent':USER_AGENT}
        session.headers.update({'Referer':BASE_URL})
        req = session.get(BASE_URL)
        session.headers.update({'X-CSRFToken':req.cookies['csrftoken']})
        login_data = {'username': USERNAME, 'password': PASSWORD}
        login = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        login_text = json.loads(login.text)
        print(login_text)
        if not login_text['authenticated']:
            raise PermissionError()
        req = session.get('https://www.instagram.com/')
        session.headers.update({'X-CSRFToken':req.cookies['csrftoken']})
        response = session.get(media_url).json()
        return response['data']['reels_media']
    except PermissionError:
        log_update(key, '426 Failed to login.', login_text)
    except Exception as e:
        log_update(key, '502 get_reels_media FAILURE', str(e))

def get_stories(reels_media, key):
    file_array = []
    index = [x.isdigit() for x in key].index(True)
    username = key[:index]
    try:
        reels_media = reels_media[0]
        items = reels_media['items']
        for item in items:
            if not item['is_video']:
                url = item['display_resources'][0]['src']
                save_response = save_to_local(url, file_array, username)
                print('DOWNLOAD:['+url+']')
            else:
                url = item['video_resources'][0]['src']
                save_response = save_to_local(url, file_array, username)
                print('DOWNLOAD:['+url+']')
            print('[^]-> ' + save_response)
        return file_array
    except IndexError:
        log_update(key,'427 No Stories.','User does not have any stories.')
    except Exception as e:
        log_update(key, '504 get_stories FAILURE.', str(e))


def save_to_local(url, file_array, username):
    LOCAL_FOLDER = username +'/'
    try:
        str1= url.split('/')[-1]
        index = str1.find('?')
        str2 = str1[0:index]
        out_file = LOCAL_FOLDER + str2
        try:
            urllib.request.urlretrieve(url,out_file)
            file_array.append(out_file)
            return 'SAVE SUCCESFUL'
        except Exception as e:
            return ('SAVE FAIL | [' + str(e) +']')
    except:
        return 'Unexpected error occured (save_to_local FAILURE)'

def upload_to_s3(file_array, key):
    try:
        s3 = boto3.resource('s3')
        for image in file_array:
            print('UPLOAD:['+image+']')
            try:
                data = open(image, 'rb')
                s3.Bucket(BUCKET_NAME).put_object(Key=image, Body=data)
                print('[^]-> UPLOAD SUCCESFUL')
            except Exception as e:
                print('[^]-> UPLOAD FAIL | [' + e+']')
        return BUCKET_NAME
    except Exception as e:
        log_update(key, '505 upload_to_s3 FAILURE.', str(e))

def log_create(key):
    localtime = time.localtime(time.time())
    localtime = str(localtime.tm_year) + '-' + str(localtime.tm_mon) + '-' + str(localtime.tm_mday) + ' ' + str(localtime.tm_hour) + ':'+ str(localtime.tm_min) + ':' + str(localtime.tm_sec) + ' +0' + str(int(- time.timezone / 36))
    with open("story-logs.json", "r+") as logs_file:
        logs = json.load(logs_file)
        logs[key] = {'status':'Waiting','message':'Waiting for proccess to finish','requested_at':localtime, 'finished_at':'-', 'bucket_name':BUCKET_NAME, 'bucket_url':'https://s3.console.aws.amazon.com/s3/buckets/' + BUCKET_NAME}
        logs_file.seek(0)
        logs_file.truncate()
        logs_file.write(json.dumps(logs))
        logs_file.close()

def log_update(key, status, message):
    localtime = time.localtime(time.time())
    localtime = str(localtime.tm_year) + '-' + str(localtime.tm_mon) + '-' + str(localtime.tm_mday) + ' ' + str(localtime.tm_hour) + ':'+ str(localtime.tm_min) + ':' + str(localtime.tm_sec) + ' +0' + str(int(- time.timezone / 36))
    with open("story-logs.json", "r+") as logs_file:
            logs = json.load(logs_file)
            logs[key]['status'] = status
            logs[key]['message'] = message
            logs[key]['finished_at'] = localtime
            logs_file.seek(0)
            logs_file.truncate()
            logs_file.write(json.dumps(logs))
            logs_file.close()
    clean_stories(key)

def clean_stories(key):
    try:
        index = [x.isdigit() for x in key].index(True)
        username = key[:index]
        print('CLEAN: ['+username+']')
        shutil.rmtree(username)
        print('[^]-> CLEAN SUCCESFUL')
    except Exception as e:
        localtime = time.localtime(time.time())
        localtime = str(localtime.tm_year) + '-' + str(localtime.tm_mon) + '-' + str(localtime.tm_mday) + ' ' + str(localtime.tm_hour) + ':'+ str(localtime.tm_min) + ':' + str(localtime.tm_sec) + ' +0' + str(int(- time.timezone / 36))
        with open("story-logs.json", "r+") as logs_file:
                logs = json.load(logs_file)
                logs[key]['status'] = '506 clean_stories FAILURE.'
                logs[key]['message'] = '!!! MANUAL DELETE REQUIRED !!! ' + str(e)
                logs[key]['finished_at'] = localtime
                logs_file.seek(0)
                logs_file.truncate()
                logs_file.write(json.dumps(logs))
                logs_file.close()

def main(unique_key):
    # Start of program
    account_id = get_account_id(unique_key)
    reels_media = get_reels_media(account_id, unique_key)
    file_array = get_stories(reels_media, unique_key)
    upload_to_s3(file_array, unique_key)

    # Update the log
    log_update(unique_key, '200 OK', 'Success')

class Storyly(object):
    def on_get(self, req, resp):
        try:
            username = req.params['u']
        except:
            raise falcon.HTTPMissingParam('u')
        try:
            os.mkdir(username)
        except Exception as e:
            raise falcon.HTTPInternalServerError(title = '505 A Process is already in progress.', description = str(e))
        # Create the log
        time_key = time.time()
        unique_key = username + str(int(time_key))
        log_create(unique_key)

        Process(target=main, args=(unique_key,)).start()
        resp.content_type = 'json'
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'key':unique_key})

class Status(object):
    def on_get(self,req,resp):
        try:
            key = req.params['key']
        except:
            raise falcon.HTTPMissingParam('key')
        with open("story-logs.json", "r+") as logs_file:
            logs = json.load(logs_file)
            logs_file.close()
        if key in logs:
            resp.content_type = 'json'
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(logs[key])
        else:
            raise falcon.HTTPBadRequest(description='No processes with key ' +str(key)+ ' found.')

# Create the Falcon application object
app = falcon.API()

# Instantiate the TestResource class
story_resource = Storyly()
status_resource = Status()

# Add a route to serve the resource
app.add_route('/story', story_resource)
app.add_route('/story/status', status_resource)