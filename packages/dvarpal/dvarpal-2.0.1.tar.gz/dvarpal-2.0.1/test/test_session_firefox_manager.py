from dvarpal.config import SessionConfig
from dvarpal.session_firefox import SessionManager

import logging
import os


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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tester = TestSessionManager()
    tester.test_session_generation_no_file()
    tester.test_session_generation_empty_file()
    tester.test_session_generation_invalid_token_in_file()

