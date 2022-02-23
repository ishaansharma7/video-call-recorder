# Video Call Recorder
This project was created using Python 3.8.10

## Setup
Install requirements.txt.\
Enter respective links and paths in .env file of each recording service.\
Install and setup obs screen recorder, add F4 key in hotkeys to start/stop recording. Check recording is working manually.\
Used chrome version 97.

## Run Project
In meeting_recorder.py file execute the function `start_recording(meeting_link, password)`, provide password in case of zoom call.

### Note
If you want to disable recording functionality make `RECORD=0` in env file, or else make sure obs is running in background else you will be promted to run obs. Obs is required in order to enter meeting.

If you want to change default database and collection name, go to one of the recording service then open bot_helper.py and do your changes in `save_to_db` function.