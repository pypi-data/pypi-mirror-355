import logging
import os

from dvarpal.config import SessionConfig
from dvarpal.session import SessionManager




import logging
import os
import time
from urllib.parse import quote

import pyotp
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

class TestSessionManager:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def test_session_generation_no_file(self):
        session_config = SessionConfig()
        print(session_config.__dict__)
        self.__delete_file_safely(session_config.access_token_file)

        session_manager = SessionManager(session_config)
        session_manager.generate_access_token()

    def test_session_generation_empty_file(self):
        session_config = SessionConfig()
        self.__create_access_token_file(session_config.access_token_file, '')

        session_manager = SessionManager(session_config)
        session_manager.generate_access_token()

    def test_session_generation_invalid_token_in_file(self):
        session_config = SessionConfig()
        self.__create_access_token_file(session_config.access_token_file, 'CRAP')

        session_manager = SessionManager(session_config)
        session_manager.generate_access_token()

    def test_session_generation_valid_token_in_file(self):
        session_manager = SessionManager(SessionConfig())
        session_manager.generate_access_token()

    def __delete_file_safely(self, file_path):
        try:
            os.remove(file_path)
            self.logger.info(f"File {file_path} deleted successfully.")
        except FileNotFoundError:
            self.logger.info(f"File {file_path} does not exist.")
        except Exception as e:
            self.logger.info(f"An error occurred while deleting the file: {e}")

    def __create_access_token_file(self, file_path, content):
        try:
            with open(file_path, 'w') as file:
                file.write(content)
            self.logger.info(f"File created at: {file_path} with content '{content}'.")
        except Exception as e:
            self.logger.info(f"An error occurred while creating the file: {e}")

    def foochoda(self):
        options = uc.ChromeOptions()
        # options.add_argument("--headless") # Do not enable this. Fails detecting OTP input
        options.add_argument(f"--headless")
        options.add_argument(f"--user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1")
        driver = uc.Chrome(options=options)
        try:

            authn_url = ('https://practicetestautomation.com/practice-test-login/')
            driver.get(authn_url)

            phone_no = driver.find_element(By.NAME, "username")
            phone_no.send_keys('student')
            get_otp_btn = driver.find_element(By.NAME, "password")
            get_otp_btn.send_keys('Password123')
            submit = driver.find_element(By.ID, "submit")
            submit.click()
            # driver.implicitly_wait(10)
            time.sleep(3)

            otp = driver.find_element(By.XPATH, "/html/body/div/div/section/div/div/article/div[2]/p[1]/strong")
            text = otp.text
            print(f'outcome = {text}')
        finally:
            if driver is not None:
                driver.close()
                driver.quit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tester = TestSessionManager()
    # tester.foochoda()
    tester.test_session_generation_no_file()
    tester.test_session_generation_empty_file()
    tester.test_session_generation_invalid_token_in_file()

