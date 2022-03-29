from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from os.path import join, dirname
import os
import time

opt = Options()
opt.headless = True
opt.add_argument('--no-sandbox')
opt.add_argument('--disable-dev-shm-usage')
opt.add_argument('--disable-gpu')
opt.add_argument('--window-size=1920,1080')


main_path = os.getcwd()
print('************')
print(main_path)
driver_path = os.path.join(main_path, 'geckodriver')
print(driver_path)

service = Service(driver_path)
driver = webdriver.Firefox(service=service, options=opt)

# meeting link
try:
    driver.get('https://accounts.google.com/ServiceLogin?')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]'))).send_keys('meetingbotai@gmail.com')
    # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]'))).send_keys('gcp@ezeiatech.com')
    print('email entered')
    driver.save_screenshot('../storage/email.png')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierNext"]/div/button'))).click()
    time.sleep(3)
    # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))).send_keys('Ezeia@1234')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))).send_keys('gurgaon48')
    print('password entered')
    driver.save_screenshot('../storage/password.png')
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="passwordNext"]/div/button'))).click()
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="phoneNumberId"]'))).send_keys('+91 9711350236')
    print('phone number section')
    driver.save_screenshot('../storage/phone_number.png')
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idvanyphonecollectNext"]/div/button/span'))).click()
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idvAnyPhonePin"]'))).send_keys(input('enter pin: '))
    print('otp entered')
    driver.save_screenshot('../storage/otp.png')
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idvanyphoneverifyNext"]/div/button'))).click()
    print('worked')
    time.sleep(5)
    driver.save_screenshot('../storage/worked.png')
except Exception as e:
    print(e)
    time.sleep(5)
    driver.save_screenshot('../storage/failure.png')