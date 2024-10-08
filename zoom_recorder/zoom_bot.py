import os, signal, subprocess
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
from zoom_recorder.bot_helper import login_details, name_modifier, mic_status, speaking_operations, find_process_id_by_name, fault_capture, toggle_recording, register_meeting_in_db, update_to_db
from time import time, ctime, sleep



def master(meeting_link: str, password: str, client_name='default_client'):
    print('started')

    # paths
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    main_path = os.getcwd()
    driver_path = os.path.join(main_path, os.environ.get('DRIVER'))

    retry_login = int(os.environ.get('RETRY'))                  # number of retries in case of login failure
    record_video = os.environ.get('RECORD_VIDEO') == '1'        # enable/disable recording feature
    record_audio = os.environ.get('RECORD_AUDIO') == '1'        # enable/disable recording feature
    wait_sec = int(os.environ.get('WAIT_SEC'))                  # general waiting time for html components to load
    admit_wait = int(os.environ.get('ADMIT_WAIT'))              # waiting time for admit
    audio_cmd = os.environ.get('SUBPROCESS_CMD')                # subrocess command for audio recording
    volume = os.environ.get('VOLUME')                           # perssistent volume path
    update_interval = int(os.environ.get('UPDATE_INTERVAL'))    # interval to update data in db


    # meeting link
    meeting_id = login_details(meeting_link)


    # check if OBS is running
    if record_video: find_process_id_by_name('obs')
    if record_video: print('OBS found')


    # camera and mic permissions
    opt = Options()
    opt.headless = True
    opt.add_argument('--no-sandbox')
    opt.add_argument('--disable-dev-shm-usage')
    opt.add_argument('--disable-gpu')
    opt.add_argument('--window-size=1920,1080')
    opt.add_experimental_option("prefs", {
        # "profile.default_content_setting_values.media_stream_mic": 1,
        # "profile.default_content_setting_values.media_stream_camera": 1,
    })


    # chrome driver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=opt)


    def login_process(retry_login: int):

        if not retry_login: exit()
        driver.get(f'https://us04web.zoom.us/wc/join/{meeting_id}?')
        print('trying to login')

        # login code
        try:
            WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.XPATH, '//*[@id="inputname"]'))).send_keys(os.environ.get('BOT_NAME'))
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="joinBtn"]'))).click()
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.ID, "inputpasscode"))).send_keys(password)
            driver.find_element(by=By.ID, value='joinBtn').click()
            driver.save_screenshot('ss1.png')
        except Exception:
            print('error in logging')
            driver.save_screenshot('ss2.png')
            fault_capture('error ocurred while loging into zoom', meeting_link, volume, meeting_id)
            if retry_login: login_process(retry_login-1)

    login_process(retry_login)
    print('succesfully loged in')

    # after entering call within 200 seconds, enable footer and open participants list
    try:
        hidden_bar = WebDriverWait(driver, admit_wait).until(EC.presence_of_element_located((By.CLASS_NAME, 'video-avatar__avatar')))
        driver.execute_script('document.getElementById("wc-footer").className = "footer";')
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wc-footer"]/div/div[2]/div[1]/button'))).click()
        driver.save_screenshot('ss3.png')
    except Exception:
        print('error occured, not able to open participants list in time')
        fault_capture('error occured, not able to open participants list in time', meeting_link, volume, meeting_id)
        exit()


    # starting screen recorder
    if record_video: toggle_recording('start')
    

    # starting time
    call_start_timestamp = time()
    call_start_time = ctime(call_start_timestamp)
    audio_name = meeting_id + '_' + str(call_start_time).replace(' ', '_') + '_' + client_name.replace(' ', '_') + '.mp3'


    # starting audio recorder
    if record_audio: p = subprocess.Popen('exec ' + audio_cmd + volume + audio_name, stdout=subprocess.PIPE, shell=True)

    MID = register_meeting_in_db(call_start_time, meeting_link, meeting_id, client_name)

    # variables
    name_keeper_dict = dict()       # keeps the count of same names
    participants_dict = dict()      # keeps the track of each participants
    participants_data = dict()      # speaking data of each participants
    left_meeting = dict()
    timeline = list()
    meeting_running = True


    def regular_update_db():
        while meeting_running:
            update_to_db({'start_time': call_start_time, 'current_time': ctime(), 'status':'ongoing'}, name_keeper_dict,
            participants_dict, participants_data, meeting_link, left_meeting ,MID, timeline, audio_name, meeting_id, client_name)
            sleep(update_interval)
        print('final update to db')
        update_to_db({'start_time': call_start_time, 'end_time': ctime(), 'status':'ended'}, name_keeper_dict,
        participants_dict, participants_data, meeting_link, left_meeting ,MID, timeline, audio_name, meeting_id, client_name)
        return


    # check for call over, exit all operations
    def call_ended():
        try: # when you are removed by host     /html/body/div[12]/div/div/div/div[1]/div
            title = driver.find_element(By.CLASS_NAME, 'zm-modal-body-title')
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
            try:
                person_name, speaking = mic_status(driver, participant_id)
            except Exception:
                left_meeting[last_name] = time()-call_start_timestamp
            if person_name == 'destroy subprocess':
                # make speaking = false, left = True, store info in left_meeting
                print('destroy subprocess')
                left_meeting[last_name] = time()-call_start_timestamp
                speaking_operations(last_name, False, call_start_timestamp, participants_data, timeline)
                return
            # DO YOUR OPERATIONS HERE FOR EACH PARTICIPANT (USE speaking BOOLEAN)
            last_name = person_name
            speaking_operations(person_name, speaking, call_start_timestamp, participants_data, timeline)


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
    
    threading.Thread(target=regular_update_db).start()
    update_participants()
    meeting_running = False


    # ending screen recorder
    if record_video: toggle_recording('stop')
  
  
    # ending audio recorder
    if record_audio: os.kill(p.pid+1, signal.SIGTERM)


    # call end time
    call_end_time = ctime()
    duration_dict = {'start_time': call_start_time, 'end_time': call_end_time, 'status':'ended'}


    # terminal output
    print(duration_dict)
    print()
    print(name_keeper_dict)
    print()
    print(list(participants_dict.keys()))
    print()
    print(participants_data)
    print()
    print(left_meeting)


    # saving to cloud mongo db
    # save_to_db(duration_dict, name_keeper_dict, participants_dict, participants_data, meeting_link, volume, left_meeting, timeline, audio_name, meeting_id)