# Dvarpal
'Dvarpal' (Sanskrit: द्वारपाल) means 'door guard'. Davrpal aims to provide automated 
login mechanism for Indian stock brokers. 

<!-- TOC -->
* [Dvarpal](#dvarpal)
  * [Supported Brokers](#supported-brokers)
  * [Installation](#installation)
  * [Configuration](#configuration)
  * [Usage](#usage)
<!-- TOC -->

## Supported Brokers

1. Upstox 

Dvarpal is designed so that support for more brokers can be added easily. 

## Installation
```commandline
pip install dvarpal
```

## Prerequisite
Dvarpal uses Selenium + Firefox ESR + Gecko Driver to perform automated logins. 
Firefox ESR and Gecko Driver have to be installed on operating system. For linux, 
this is automated in the script [install-firefox-esr-geckodriver.sh](etc/install-firefox-esr-geckodriver.sh)

For Windows and Mac, it is left upto the user to perform similar installations. 

## Configuration

Dvarpal picks up configration file from `${HOME}/dvarpal.yaml` file. A sample file for 
Upstox is shared below. For more samples, refer to [config_samples](./config_samples) directory. 

```yaml
authn_url: https://api.upstox.com/v2/login/authorization/dialog
authz_url: https://api.upstox.com/v2/login/authorization/token

# The following properties are part of upstox app created for API access
client_id: <your-client-id>
client_secret: <your-client-secret>
redirect_uri: <your-redirect-url>

# TOTP secret key generated using https://help.upstox.com/support/solutions/articles/260343-what-is-totp-and-how-to-enable-totp-for-my-account-
totp_secret_key: <your TOTP secret key>

mobile: <your registered mobile number>
pin: <your pin>
```

## Usage

Starting version 2.0.0, Dvarpal will use Firefox ESR + Gecko Driver. 
Support for Google Chrome and Undetected Chromedriver have been deprecated. 
In version 2.0.1, support for Chrome will be removed. 

```python
from dvarpal.session_firefox import SessionManager

session_manager = SessionManager()
session_manager.generate_access_token()  # to generate a new access token
session_manager.is_session_valid()  # to check if access token is valid
session_manager.get_access_token()  # get the actual access token string
```

Upon generating an access_token, it is saved to text file `${HOME}/dvarpal_session`. 
Before generating a new access token, dvarpal checks the file. If file exists, it loads 
the access token from file and uses it. If the 
token is expired or invalid, dvarpal generates a new one.
