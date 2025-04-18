from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import time

# Message & phone
phone_number = "+************"  # Replace with the recipient's phone number
message = "✅ Auto-message with working wait strategy"
encoded_msg = urllib.parse.quote(message)
url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_msg}"

# Chrome config
options = Options()
options.add_argument(r"--user-data-dir=C:\Users\LARA_B\WhatsAppSession")
options.add_argument("--profile-directory=Profile1")
options.add_argument("--start-maximized")

# Start driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

print("🔄 Waiting for WhatsApp Web to load...")

try:
    # Wait for up to 30 seconds until the input box appears
    wait = WebDriverWait(driver, 30)
    input_box = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@contenteditable='true' and @data-tab='10']")
    ))
    input_box.send_keys(Keys.ENTER)
    print("✅ Message sent using ENTER")
except Exception as e:
    print("❌ Failed to send message:", e)

time.sleep(5)
driver.quit()
