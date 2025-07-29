import logging
import os

import yaml


class SessionConfig:

    def __init__(self):
        cfg = SessionConfig._load_config_from_file()
        self.access_token_file = cfg.get('access_token_file') if cfg.get('access_token_file') else SessionConfig._get_access_token_file_location()

        self.authn_url: str = cfg['authn_url']
        self.authz_url: str = cfg['authz_url']
        self.redirect_uri: str = cfg['redirect_uri']
        self.session_validation_url: str = cfg['session_validation_url']
        self.browser_useragent = cfg.get('browser_useragent') if cfg.get('browser_useragent') is not None else 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'
        self.browser_headless = False if cfg.get('browser_headless') is None else cfg.get('browser_headless')

        self.client_id: str = cfg['client_id']
        self.client_secret: str = cfg['client_secret']
        self.mobile: str = cfg['mobile']
        self.totp_secret_key: str = cfg['totp_secret_key']
        self.pin: str = cfg['pin']

    @staticmethod
    def _load_config_from_file():
        # Choose home directory env variable based on OS. os.name = 'nt' for windows.
        config_file = os.path.join(SessionConfig.get_home_dir(), ".dvarpal", 'dvarpal.yaml')
        if not os.path.exists(config_file):
            pass

        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        # logging.info(f'Loaded dvarpal config from file {config_file}')
        return config_data

    @staticmethod
    def _get_access_token_file_location():
        return os.path.join(SessionConfig.get_home_dir(), ".dvarpal", "dvarpal_session")

    @staticmethod
    def get_home_dir():
        return os.getenv('USERPROFILE') if os.name == 'nt' else os.getenv('HOME')

