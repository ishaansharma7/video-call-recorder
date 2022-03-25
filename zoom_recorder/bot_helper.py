import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from pymongo import MongoClient
from bson import ObjectId
import psutil
# from pynput.keyboard import Key, Controller
import json


# read login details from env file
def login_details(meeting_link: str):
    URL = meeting_link
    URL = URL.split('/j/')[1].split('?')[0]
    return URL


# check if OBS is running
def find_process_id_by_name(process_name):
    list_of_process_objects = []
    while True:
    # Iterate over the all the running process
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
                # Check if process name contains the given name string.
                if process_name.lower() in pinfo['name'].lower():
                    list_of_process_objects.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if len(list_of_process_objects) > 0:
            return len(list_of_process_objects)
        print('OBS not found')
        time.sleep(.5)


# error/exception during login or entery
def fault_capture(msg: str, URL: str, volume:str, meeting_id:str):
    error_dict = {
        'message': msg,
        'event': 'error',
        'type': 'zoom_call',
        'meeting_id': meeting_id,
        'joining link': URL,
        'time': time.ctime()
    }
    print('error occured')
    try:
        with open(volume+'recent_call_error.txt', 'a') as convert_file:
            convert_file.write('\n\n\n')
            convert_file.write(json.dumps(error_dict, indent=4))
    except Exception:
        print('unable to store error data locally')
    try:
        cluster = os.environ.get('CLUSTER')
        client = MongoClient(cluster)
        db = client['meetingLiveStreaming']
        db.meeting_collection.insert_one(error_dict)
        print('successfully inserted error data in cloud db')
    except Exception:
        print('unable to store error data on cloud db')


# start/stop screen recording
# def start_stop_recording(action: str):
#     keyboard = Controller()
#     keyboard.press(Key.f4)
#     time.sleep(.05)
#     keyboard.release(Key.f4)

def toggle_recording(action:str):
    pass
    # keyboard = Controller()
    # keyboard.press(Key.f4)
    # time.sleep(.05)
    # keyboard.release(Key.f4)
    # time.sleep(1)
    # num_of_processes = find_process_id_by_name('obs')
    # if action == 'start' and num_of_processes <= 1:
    #     print('unable to start recording, trying again')
    #     toggle_recording('start')
    # if action == 'stop' and num_of_processes > 1:
    #     print('unable to stop recording, trying again')
    #     toggle_recording('stop')


# count the number of time a name is used
def name_modifier(person_name: str, name_keeper_dict: dict):
    if person_name in name_keeper_dict:
        name_keeper_dict[person_name] = name_keeper_dict[person_name] + 1
        return name_keeper_dict[person_name]
    name_keeper_dict[person_name] = 1
    return 1


# check whether the mic symbol is changing
def mic_status(driver: object, participant_id: str):
    try:
        li = driver.find_element(by=By.ID, value=participant_id)
    except Exception as e:
        print(participant_id, 'not found')
        return 'destroy subprocess', False
    person_name = li.find_element(by=By.CLASS_NAME, value='participants-item__display-name').text
    speaking = False
    try:
        svg = li.find_element(by=By.TAG_NAME, value='svg')
        path2 = svg.find_elements(By.TAG_NAME, value='path')[1]
        value = path2.get_attribute('fill')
        if value != None:
            speaking = True
    except Exception as e:
        pass
    return person_name, speaking
    # print(person_name, 'speaking:', speaking)


# create the data for each participant
def speaking_operations(person_name: str, speaking: bool, call_start_timestamp: float, participants_data: dict, timeline: list):
    if person_name not in participants_data:
        c_time = time.time()-call_start_timestamp
        participants_data[person_name] = [{'speaking':speaking, 'current_time': c_time}]
        timeline.append([c_time, person_name, 'entered speaking' if speaking else ' entered silent'])
        return
    if participants_data[person_name][-1]['speaking'] == speaking:
        return
    else:
        c_time = time.time()-call_start_timestamp
        participants_data[person_name].append({'speaking':speaking, 'current_time': c_time})
        timeline.append([c_time, person_name, 'speaking' if speaking else 'silent'])


# insert data to cloud db
# def save_to_db(duration_dict: dict, name_keeper_dict: dict, participants_dict: dict, participants_data: dict, URL: str, volume: str, left_meeting: dict, timeline: list, audio_name:str, meeting_id:str):
#     call_summary = {
#         'call_duration': duration_dict,
#         'call_date': datetime.utcnow(),
#         'type': 'zoom_call',
#         'joining_link': URL,
#         'meeting_id': meeting_id,
#         'name_count': name_keeper_dict,
#         'participants_name': list(participants_dict.keys()),
#         'participants_left': left_meeting,
#         'participants_data': participants_data,
#         'timeline':timeline,
#         'audio_name':audio_name
#         }
#     try:
#         with open(volume+'recent_zoom_call.txt', 'a') as convert_file:
#             convert_file.write('\n\n\n')
#             convert_file.write(json.dumps(call_summary, indent=4))
#     except Exception:
#         print('error in storing data locally')
#     try:
#         cluster = os.environ.get('CLUSTER')
#         client = MongoClient(cluster)
#         db = client['meetingLiveStreaming']
#         db.meeting_collection.insert_one(call_summary)
#         print('successfully inserted data in db')
#     except Exception:
#         print('error in storing data on db')

# register in db at start of meeting
def register_meeting_in_db(call_start_time: str, URL: str, meeting_id:str, client_name:str):
    call_summary = {
        'call_duration': call_start_time,
        'type': 'zoom_call',
        'meeting_id': meeting_id,
        'joining_link': URL,
        'client_name': client_name,
        }
    try:
        cluster = os.environ.get('CLUSTER')
        client = MongoClient(cluster)
        db = client['meetingLiveStreaming']
        doc = db.meeting_collection.insert_one(call_summary)
        print('successfully registered meeting in db')
        return doc.inserted_id
    except Exception:
        print('error in registering meeting in db')
        return

# continiously update data in db
def update_to_db(duration_dict: dict, name_keeper_dict: dict, participants_dict: dict, participants_data: dict, URL: str, left_meeting: dict, MID: str, timeline: list, audio_name:str, meeting_id:str, client_name:str):
    call_summary = {
        'call_duration': duration_dict,
        'call_date': datetime.utcnow(),
        'type': 'zoom_call',
        'joining_link': URL,
        'meeting_id': meeting_id,
        'name_count': name_keeper_dict,
        'participants_name': list(participants_dict.keys()),
        'participants_left': left_meeting,
        'participants_data': participants_data,
        'timeline':timeline,
        'audio_name':audio_name,
        'client_name':client_name,
        }
    try:
        cluster = os.environ.get('CLUSTER')
        client = MongoClient(cluster)
        db = client['meetingLiveStreaming']
        db.meeting_collection.replace_one({'_id':ObjectId(MID)}, call_summary)
        print('successfully updated data in db')
    except Exception:
        print('error in updating data on db')
