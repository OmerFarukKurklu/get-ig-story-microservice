# get-ig-story-microservice
A microservice which takes an username as parameter and gets all of user's stories into a S3 bucket

## The inital goal
the goal is to get the given user's available stories. So the main project/product this microservice created for can use the stories for their sdk.

## Created with:
- **[Docker](https://www.docker.com/)**
- **[gunicorn](https://gunicorn.org/)** (WSGI server for python)
- **[Falcon](https://falconframework.org/)** (Web API framework for python)
- **[boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html?id=docs_gateway)** (Amazon Web Services SDK for Python, I used for S3 Buckets.)
- **[multiprocessing](https://docs.python.org/2/library/multiprocessing.html)** (will explain why I used this)
- [requests](https://requests.kennethreitz.org/en/master/)
- [json](https://docs.python.org/3/library/json.html)
- [urllib.request](https://docs.python.org/3/library/urllib.request.html)
- [os](https://docs.python.org/3/library/os.html)
- [shutil](https://docs.python.org/3/library/shutil.html)
- [time](https://docs.python.org/3/library/time.html)

## How it works
App uses given bot/dummy account username and password to request and get necessary cookies from instagram. Then it requests to directly query since Instagram does not have any APIs for stories. Once image sources are obtained, App then downloads them and uploads them to a S3 Bucket.

Also implemented a status endpoint. Didn't want to use a database for this simple task hence the `story-logs.json` file stores the logs for the spesific key and it can be accessed by a GET request to this endpoint.

Once a user sends a request to `/story` endpoint they recieve a key and with that key they can check for status.

With this two seperate endpoint way I can send responses immidiately and not wory about timeout errors. After the initial request to `/story` endpoint the app starts a different process and continues to response with a key. To see status of the started process, a new endpoint implementation was crucial.

#### Why I used multiprocess and not others such as multithread
- [ ] to be written.

## Usage
First replace the blanks with square brackets.

in `get-ig-story-microservice/deploy-story/src/story.py` change:
```python
BUCKET_NAME = [BUCKET_NAME] #CHANGE THIS
USERNAME = [BOT_ACCOUNT_USERNAME] #CHANGE THIS
PASSWORD = [BOT_ACCOUNT_PASSWORD] #CHANGE THIS
```
with your S3 Bucket name and Instagram bot/dummy account username-password.

---

in `get-ig-story-microservice/deploy-story/credidentals/credentials` change:
```
aws_access_key_id = [ACCESS_KEY_ID]
aws_secret_access_key = [SECRET_ACCESS_KEY]
````
with your personal acces keys from AWS

---

Since everything is in Docker, just copy this folder to server. Then locate the folder and run 

`docker image build --tag story-image:1.0 .`
- the `--tag` just names the image and the `:1.0` represents the version, you can change them if you'd like.

Docker, with the `requirements.txt` file should install all the necessary libraries. Once done, run 

`docker container run -d -p 8080:80 --name story-microservice story-image:1.0`
- the `-d` or in other words `--detach` tag detaches the container from terminal and runs in background, you might want to remove it if you'd like to see the logs and messages from the app, you can also use [screen](https://www.gnu.org/software/screen/) start a new screen with different process and run the container on there, since it is a different process if you don't kill the screen tab you ran the container, the container will still run even after you disconnect from the ssh with your server, I would strongly recommend using screen since it is really easy to menage between containers and helps checking for log messages inside the container from the app, you can also switch to screens even after you closed you ssh connection and reopened it.
- the `-p` or `--publish` tag connects the ports 8080 of the original machine and port 80 of the container since I exposed port 80 in the Dockerfile.

Once done the microservice is set and running.

You can use the service with a GET request to the IP address of the machine you are using, send a GET requast to

`[IP ADDRESS OF YOUR SERVER]:8080/story?u=[INSTAGRAM ACCOUNT USERNAME]`

It should return you a key such as `username123456789`. Using this key you can check the process inside the server for status updates and check for error messages. Send a GET request to the status endpoint `/story/status`

`[IP ADDRESS OF YOUR SERVER]:8080/story/status?key=[KEY]`

## Future work
- [ ] Change the logs system with [SQLite](https://www.sqlite.org/index.html)
- [ ] Comment the code with detailed descriptions on which function does what and why.
- [ ] Write the "Why I used multiprocess and not others such as multithread" part. Maybe like a Medium blog for this?
- [ ] ?
