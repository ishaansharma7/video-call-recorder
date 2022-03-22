# from pynput.keyboard import Key, Controller
import psutil
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pymongo import MongoClient
import time
import json


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
def fault_capture(msg: str, URL: str):
    error_dict = {
        'event': 'error',
        'type': 'google meet',
        'message': msg,
        'joining link': URL,
        'time': time.ctime()
    }
    print('error occured', msg)
    try:
        with open('recent_call_error.txt', 'a') as convert_file:
            convert_file.write('\n\n\n')
            convert_file.write(json.dumps(error_dict, indent=4))
    except Exception:
        print('unable to store error data locally')
    try:
        cluster = os.environ.get('CLUSTER')
        client = MongoClient(cluster)
        db = client.meeting_database
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
        participant_div_tag = driver.find_element(By.CSS_SELECTOR, value=f".cxdMu[data-participant-id='{participant_id}']")
    except Exception:
        print(participant_id, 'not found')
        return 'destroy subprocess', False
    person_name = participant_div_tag.find_element(By.TAG_NAME, value='span').text
    speaking = True
    try:
        participant_div_tag.find_element(By.CLASS_NAME, value='gjg47c')
        speaking = False
    except NoSuchElementException:
        pass
    return person_name, speaking


# create the data for each participant
def speaking_operations(person_name: str, speaking: bool, call_start_timestamp: float, participants_data: dict):
    if person_name not in participants_data:
        participants_data[person_name] = [{'speaking':speaking, 'current_time': time.time()-call_start_timestamp}]
        return
    if participants_data[person_name][-1]['speaking'] == speaking:
        return
    else:
        participants_data[person_name].append({'speaking':speaking, 'current_time': time.time()-call_start_timestamp})


# insert data to cloud db
def save_to_db(duration_dict: dict, name_keeper_dict: dict, participant_id_name_dict: dict, participants_data: dict, URL: str):
    call_summary = {
        'call duration': duration_dict,
        'type': 'google meet',
        'joining link': URL,
        'name count': name_keeper_dict,
        'participants name': list(participant_id_name_dict.values()),
        'participants data': participants_data
        }
    try:
        with open('recent_google_meet.txt', 'a') as convert_file:
            convert_file.write('\n\n\n')
            convert_file.write(json.dumps(call_summary, indent=4))
    except Exception:
        print('error in storing data locally')
    try:
        cluster = os.environ.get('CLUSTER')
        client = MongoClient(cluster)
        db = client.meeting_database
        db.meeting_collection.insert_one(call_summary)
        print('successfully inserted data in cloud db')
    except Exception:
        print('error in storing data on cloud')