import os
from os.path import join, dirname
from dotenv import load_dotenv
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from google_meet_recorder.bot_helper import fault_capture, name_modifier, mic_status, speaking_operations, save_to_db, toggle_recording, find_process_id_by_name
import json


def master(meeting_link: str):

    # paths
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    main_path = os.getcwd()
    driver_path = os.path.join(main_path, os.environ.get('DRIVER'))

    retry_login = int(os.environ.get('RETRY'))          # number of retries in case of login failure
    record = os.environ.get('RECORD') == '1'            # enable/disable recording feature
    wait_sec = int(os.environ.get('WAIT_SEC'))          # general waiting time for html components to load
    admit_wait = int(os.environ.get('ADMIT_WAIT'))      # waiting time for admit
    hear_window = float(os.environ.get('HEAR_WINDOW'))  # window span for listening
    volume = os.environ.get('VOLUME')


    # check if OBS is running
    if record: find_process_id_by_name('obs')
    if record: print('OBS found')


    # camera and mic permissions
    opt = Options()
    opt.headless = True
    opt.add_argument('--no-sandbox')
    opt.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
    })
    opt.add_argument('--disable-blink-features=AutomationControlled')

    # chrome driver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=opt)
    driver.maximize_window()
    # driver.set_window_size(1366, 768)


    # meeting link
    URL = meeting_link


    def email_login_process(retry_login: int):
        print('trying to login')
        if not retry_login: exit()
        driver.get('https://accounts.google.com/ServiceLogin?')

        # google login
        try:
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]'))).send_keys(os.environ.get('EMAIL'))
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierNext"]/div/button'))).click()
            time.sleep(3)
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))).send_keys(os.environ.get('PASSWORD'))
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="passwordNext"]/div/button'))).click()
        except Exception:
            fault_capture('unable to login using gmail id', URL)
            driver.save_screenshot(volume+'ss.png')
            exit()
            if retry_login: email_login_process(retry_login-1)


    def meeting_login_process(retry_login: int):

        if not retry_login: exit()
        driver.get(URL)
        print('trying to enter meeting')
        # wait for google meet to load properly
        try:
            time.sleep(1)
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div[9]/div[3]/div/div/div[3]/div/div/div[1]/div[1]/div/div[4]/div[2]/div/div'))).click()
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/c-wiz/div/div/div[9]/div[3]/div/div/div[3]/div/div/div[2]/div/div[2]/div/div[1]/div[1]'))).click()
        except Exception:
            fault_capture('unable to join meeting', URL)
            driver.save_screenshot(volume+'ss2.png')
            if retry_login: meeting_login_process(retry_login-1)


    email_login_process(retry_login)
    print('successfully logged in')
    # time.sleep(5)
    # meeting_login_process(retry_login)
    # print('successfully entered meeting')


    # # open participants list
    # try:
    #     WebDriverWait(driver, admit_wait).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ow3"]/div[1]/div/div[9]/div[3]/div[10]/div[3]/div[3]/div/div/div[2]/span/button'))).click()
    # except Exception:
    #     fault_capture('unable to enter meeting and open participants list', URL)
    #     exit()


    # # starting screen recorder
    # if record: toggle_recording('start')


    # # starting time
    # call_start_timestamp = time.time()-1
    # call_start_time = time.ctime(call_start_timestamp)


    # # variables
    # name_keeper_dict = dict()               # keeps the count of same names
    # participant_id_name_dict = dict()       # html id to name relation
    # participants_data = dict()              # speaking data of each participants


    # # check for meeting over, exit all operations
    # def meeting_ended():
    #     try:
    #         driver.find_element(by=By.XPATH, value='//*[@id="ow3"]/div[1]/div/div[9]/div[3]/div[10]/div[2]/div/div[7]/span/button')
    #     except NoSuchElementException:
    #         return True
    #     return False


    # # subprocess for each participant
    # def participant_div_subprocess(participant_id: str):
    #     last_name = ''
    #     while True:
    #         if meeting_ended(): return
    #         person_name, speaking = mic_status(driver, participant_id)
    #         if person_name == 'destroy subprocess':
    #                 # print(person_name, participant_id)
    #             speaking_operations(last_name, False, call_start_timestamp, participants_data)
    #             return
    #         last_name = participant_id_name_dict[participant_id]
    #         speaking_operations(participant_id_name_dict[participant_id], speaking, call_start_timestamp, participants_data)
    #         if speaking: time.sleep(hear_window)


    # # add new paricipants and start thier subprocess
    # def update_participants():
    #     while True:
    #         if meeting_ended(): return
    #         try:
    #             names_ul = driver.find_element(By.XPATH, '//*[@id="ow3"]/div[1]/div/div[9]/div[3]/div[4]/div[2]/div[2]/div[2]/div[3]/div')
    #             participants_html_list = names_ul.find_elements(By.CLASS_NAME, value='cxdMu')
    #             for participant_div_tag in participants_html_list:
    #                 person_name = participant_div_tag.find_element(By.TAG_NAME, value='span').text
    #                 participant_id = str(participant_div_tag.get_attribute('data-participant-id'))
    #                 if participant_id in participant_id_name_dict:
    #                     continue
    #                 person_name = str(person_name) + ' #' + str(name_modifier(person_name, name_keeper_dict))
    #                 participant_id_name_dict[participant_id] = person_name
    #                 print(person_name, 'found')
    #                 # initiate sub process for participant_div_tag (each participant)
    #                 threading.Thread(target=participant_div_subprocess, args=[participant_id]).start()
    #         except Exception as e:
    #             print('* exception in update_participants for loop *')

    # update_participants()


    # # ending screen recorder
    # if record: toggle_recording('stop')


    # # call end time
    # call_end_time = time.ctime()
    # duration_dict = {'start time': call_start_time, 'end time': call_end_time}


    # # terminal output
    # print(duration_dict)
    # print()
    # print(name_keeper_dict)
    # print()
    # print(participant_id_name_dict)
    # print()
    # print(participants_data)


    # # saving to cloud mongo db
    # save_to_db(duration_dict, name_keeper_dict, participant_id_name_dict, participants_data, URL)