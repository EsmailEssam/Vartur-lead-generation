import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

######################################## OpenAI ########################################
# Load environment variables
load_dotenv(override=True)

# Get OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

######################################## Exception ########################################
class LinkedInLoginError(Exception):
    """Custom exception for LinkedIn login failures"""
    pass

class InstagramLoginError(Exception):
    """Custom exception for Instagram login failures"""
    pass

class InvalidCredentialsError(InstagramLoginError):
    """Specific exception for invalid credentials"""
    pass

######################################## Logger ########################################
# Configure console-only logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

######################################## Get Current Path ########################################
try:
    current_path = os.path.dirname(os.path.abspath(__file__))
except:
    current_path = '.'

######################################## Initialize Driver ########################################
gecko_driver = 'driver/geckodriver.exe'
def init_driver(gecko_driver='', load_images=True, is_headless=False):

    options = Options()
    options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
    options.set_preference("media.volume_scale", "0.0")
    options.set_preference("dom.webnotifications.enabled", False)
    
    user_agent = 'Mozilla/5.0 (X11; ; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'
    options.set_preference("general.useragent.override", user_agent)
    
    if not load_images:
        options.set_preference('permissions.default.image', 2)
    
    if is_headless:
        options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Firefox(service = Service(executable_path=os.path.join(current_path, 'driver', 'geckodriver.exe')),
                            options=options)
    
    return driver
