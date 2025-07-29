import logging
import os
import time
from urllib.parse import quote

import pyotp
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from dvarpal.config import SessionConfig


class SessionManager:

    def __init__(self, config: SessionConfig = SessionConfig()):
        """
        If config object is None, loads config from `${HOME_DIR}/dvarpal.yaml.
        :param config:
        """
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__access_token = ''
        self.__config = config

    def generate_access_token(self):

        # check if session_token file exists. If it exists, load token from file.
        self._load_access_token_from_file()

        if self.__access_token is not None and self.is_session_valid():
            self.__logger.info("Access token is still valid. Nothing to do.")
            return

        access_token = self._get_access_token()
        self.__access_token = access_token
        self.__logger.info(f'New access token acquired: {access_token}' )
        self._save_access_token(access_token)

    def get_access_token(self):
        return self.__access_token

    def is_session_valid(self) -> bool:
        url = self.__config.session_validation_url

        headers = {
            "Api-Version": "2.0",
            "Authorization": f"Bearer {self.__access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            body = response.text
            self.__logger.info(f"Ping response: http-status: {response.status_code} > body: {body}")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException as e:
            self.__logger.error("Ping failed!", e)

        return False

    def _save_access_token(self, access_token: str):
        try:
            with open(self.__config.access_token_file, 'w') as file:
                file.write(access_token)
            self.__logger.info(f"Access token successfully written to {self.__config.access_token_file}")
        except Exception as e:
            raise Exception(f"Failed to save access token to file {self.__config.access_token_file}", e)

    def _load_access_token_from_file(self):
        if not os.path.exists(self.__config.access_token_file):
            return

        with open(self.__config.access_token_file, 'r') as file:
            content = file.read()
        self.__access_token = content
        self.__logger.info(f'Loaded access token from file {self.__config.access_token_file}')

    def _get_access_code(self) -> str:

        options = Options()
        # Explicitly use Firefox ESR
        options.binary_location = "/usr/bin/firefox-esr"
        if self.__config.browser_headless:
            options.add_argument("--headless")
        options.set_preference("general.useragent.override", self.__config.browser_useragent)
        # options.add_argument(f"--user-agent={self.__config.browser_useragent}")

        driver = webdriver.Firefox(options=options)
        try:

            authn_url = (f'{self.__config.authn_url}?'
                         f'response_type=code&'
                         f'client_id={self.__config.client_id}&'
                         f'redirect_uri={quote(self.__config.redirect_uri)}')
            driver.get(authn_url)
            time.sleep(5)
            self.__logger.info('==> browser launched')

            phone_no = driver.find_element(By.ID, "mobileNum")
            phone_no.send_keys(self.__config.mobile)
            self.__logger.info('==> mobile number entered')

            get_otp_btn = driver.find_element(By.ID, "getOtp")
            get_otp_btn.submit()
            self.__logger.info('==> OTP requested')
            time.sleep(5)

            otp = driver.find_element(By.ID, "otpNum")
            totp = pyotp.TOTP(self.__config.totp_secret_key).now()
            otp.send_keys(totp)
            self.__logger.info('==> TOTP entered')
            continue_btn = driver.find_element(By.ID, "continueBtn")
            continue_btn.submit()
            self.__logger.info('==> TOTP submitted')
            time.sleep(5)

            pin = driver.find_element(By.ID, "pinCode")
            pin.send_keys(self.__config.pin)
            self.__logger.info('==> PIN entered')
            submit = driver.find_element(By.ID, "pinContinueBtn")
            submit.click()
            self.__logger.info('==> PIN submitted')
            time.sleep(5)

            url = driver.current_url
            initial_access_code = url.split('code=')[1]
            access_code = initial_access_code.split('&')[0]
            self.__logger.debug(f'access_code: {access_code}')
        finally:
            if driver is not None:
                driver.close()
                driver.quit()

        return access_code

    def _get_access_token(self) -> str:
        s = requests.Session()
        access_code = self._get_access_code()
        # header data that needs to be sent to the post method
        headers = {"accept": "application/json", "Api-Version": "2.0",
                   "content-type": "application/x-www-form-urlencoded"}
        # the main data that needs to be sent to the post method
        data = {'code': access_code,
                'client_id': self.__config.client_id,
                'client_secret': self.__config.client_secret,
                'redirect_uri': self.__config.redirect_uri,
                'grant_type': 'authorization_code'
                }
        # post method consists of three parameters url, header and data
        resp = s.post(url=self.__config.authz_url, headers=headers, data=data)
        # test for the status code else throws error
        assert resp.status_code == 200, f"Error in r3:\n {resp.json()}"

        json_response = resp.json()
        # read the access token from the json response
        access_token = json_response['access_token']
        self.__logger.debug(f'access_token: {access_token}')
        return access_token
