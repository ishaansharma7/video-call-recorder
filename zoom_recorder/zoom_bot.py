import os
from os.path import join, dirname
from dotenv import load_dotenv
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from zoom_recorder.bot_helper import login_details, name_modifier, mic_status, save_to_db, speaking_operations, find_process_id_by_name, fault_capture, toggle_recording
from time import time, ctime


def master(meeting_link: str, password: str):

    # paths
    main_path = os.getcwd()
    driver_path = os.path.join(main_path, 'chromedriver')
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    retry_login = int(os.environ.get('RETRY'))          # number of retries in case of login failure
    record = os.environ.get('RECORD') == '1'            # enable/disable recording feature
    wait_sec = int(os.environ.get('WAIT_SEC'))          # general waiting time for html components to load
    admit_wait = int(os.environ.get('ADMIT_WAIT'))      # waiting time for admit


    # meeting link
    URL = login_details(meeting_link)


    # check if OBS is running
    if record: find_process_id_by_name('obs')
    if record: print('OBS found')


    # camera and mic permissions
    opt = Options()
    opt.add_experimental_option("prefs", {
        # "profile.default_content_setting_values.media_stream_mic": 1,
        # "profile.default_content_setting_values.media_stream_camera": 1,
    })


    # chrome driver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=opt)
    driver.maximize_window()


    def login_process(retry_login: int):

        if not retry_login: exit()
        driver.get(f'https://us04web.zoom.us/wc/join/{URL}?')

        # login code
        try:
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="inputname"]'))).send_keys('Zoom Bot')
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="joinBtn"]'))).click()
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.ID, "inputpasscode"))).send_keys(password)
            driver.find_element(by=By.ID, value='joinBtn').click()
        except Exception:
            fault_capture('error ocurred while loging into zoom', URL)
            if retry_login: login_process(retry_login-1)

    login_process(retry_login)


    # after entering call within 200 seconds, enable footer and open participants list
    try:
        hidden_bar = WebDriverWait(driver, admit_wait).until(EC.presence_of_element_located((By.CLASS_NAME, 'video-avatar__avatar')))
        driver.execute_script('document.getElementById("wc-footer").className = "footer";')
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wc-footer"]/div/div[2]/div[1]/button'))).click()
    except Exception:
        fault_capture('error occured, not able to open participants list in time', URL)
        exit()


    # starting screen recorder
    if record: toggle_recording('start')


    # starting time
    call_start_timestamp = time()-1
    call_start_time = ctime(call_start_timestamp)


    # variables
    name_keeper_dict = dict()       # keeps the count of same names
    participants_dict = dict()      # keeps the track of each participants
    participants_data = dict()      # speaking data of each participants


    # check for call over, exit all operations
    def call_ended():
        try: # when you are removed by host
            title = driver.find_element(By.XPATH, '/html/body/div[12]/div/div/div/div[1]/div[1]')
            if title.text == 'You have been removed' or title.text == 'This meeting has been ended by host':
                return True
        except Exception:
            pass
        try: # when you leave meeting
            driver.find_element(by=By.CLASS_NAME, value='video-avatar__avatar')
        except NoSuchElementException:
            return True
        return False


    # subprocess for each particiant
    def participant_li_subprocess(participant_id: str):
        last_name = ''
        while True:
            if call_ended(): return
            person_name, speaking = mic_status(driver, participant_id)
            if person_name == 'destroy subprocess':
                speaking_operations(last_name, False, call_start_timestamp, participants_data)
                return
            # DO YOUR OPERATIONS HERE FOR EACH PARTICIPANT (USE speaking BOOLEAN)
            last_name = person_name
            speaking_operations(person_name, speaking, call_start_timestamp, participants_data)


    # add new paricipants and start thier subprocess
    def update_participants():
        while True:
            if call_ended(): return
            try:
                names_ul = driver.find_element(by=By.ID, value='participants-ul')
                participants_html_list = names_ul.find_elements(By.TAG_NAME, value='li')
            except Exception:
                continue
            try:
                for participant_li_tag in participants_html_list:
                    if participant_li_tag.text == '':
                        continue
                    participant_id = str(participant_li_tag.get_attribute('id'))
                    person_name = participant_li_tag.find_element(by=By.CLASS_NAME, value='participants-item__display-name').text
                    if person_name in participants_dict:
                        continue
                    person_name = str(person_name) + ' #' + str(name_modifier(person_name, name_keeper_dict))
                    participants_dict[person_name] = True
                    driver.execute_script(f'''let li = document.getElementById("{participant_id}");
                                            li.getElementsByClassName("participants-item__display-name")[0].innerHTML = "{person_name}";
                                            ''')
                    
                    # initiate sub process for participant_li_tag (each participant)
                    threading.Thread(target=participant_li_subprocess, args=[participant_id]).start()
                    print(person_name, participant_id, 'added')
            except Exception:
                print('* exception in update_participants for loop *')
                continue

    update_participants()


    # ending screen recorder
    if record: toggle_recording('stop')


    # call end time
    call_end_time = ctime()
    duration_dict = {'start time': call_start_time, 'end time': call_end_time}


    # terminal output
    print(duration_dict)
    print()
    print(name_keeper_dict)
    print()
    print(list(participants_dict.keys()))
    print()
    print(participants_data)


    # saving to cloud mongo db
    save_to_db(duration_dict, name_keeper_dict, participants_dict, participants_data, meeting_link)