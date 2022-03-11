# Video Call Recorder
This project was created using Python 3.8.10

## Docker Setup
run the below command on server.\
`sudo docker build -t zoom_container .`

## Setup API for running docker container
https://gitlab.com/ishaansharma7/screen_recording_api.git \
Setup the above project on server.\
Then run `python starter_api.py` \
view sample.png for endpoint and body for post request.

#
## Setup For Local Machine (Dockerless)
Install requirements.txt.\
Enter respective links and paths in .env file of each recording service.\
Install and setup obs screen recorder, add F4 key in hotkeys to start/stop recording. Check recording is working manually.\
Used chrome version 97.

## Run Project
In meeting_recorder.py file execute the function `start_recording(meeting_link, password)`, provide password in case of zoom call.

### Note
If you want to disable recording functionality make `RECORD=0` in env file, or else make sure obs is running in background else you will be promted to run obs. Obs is required in order to enter meeting.

If you want to change default database and collection name, go to one of the recording service then open bot_helper.py and do your changes in `save_to_db` function.