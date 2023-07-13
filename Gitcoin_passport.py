import random
import pandas as pd
import colorlog
import requests
import time
import string
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
import json

# Define the name of the configuration file
config_file = "config.json"

# Check if the file exists
if not os.path.exists(config_file):
    print("You run this code for first time, and you need to set parameters")
    print("You can change config at any time")

    max_workers = input("Enter how mach profile should run simultaniasly: ")
    Change_password = input("Did you need to change Twitter password? Enter '1' if 'yes', or '0' if 'no': ")
    param3 = input("Please enter the third parameter: ")

    # Create a dictionary with the parameters
    config = {"max_workers": max_workers, "Change_password": Change_password}

    # Write the configuration to a file
    with open(config_file, 'w') as f:
        json.dump(config, f)
else:
    # Load the configuration from the file
    with open(config_file, 'r') as f:
        config = json.load(f)

    max_workers = config["max_workers"]
    Change_password = config["Change_password"]


chrome_driver_path = "Gitcoin_passport/chromedriver111/chromedriver/chromedriver-win-x64.exe"
metamask_url = f"chrome-extension://cfkgdnlcieooajdnoehjhgbmpbiacopjflbjpnkm/home.html#"
data_path = "Gitcoin_passport/Data/profile_and_stamp_data.xlsx"
data_path2 = "Gitcoin_passport/Data/login_data.xlsx"
Gitcoin = "https://passport.gitcoin.co/#/"
dashboard = "https://passport.gitcoin.co/#/dashboard"
proposal1 = "https://snapshot.org/#/stgdao.eth/proposal/0x85c675f303a69df297e1fdcf6dc2845366a8672362e946150ba4a4d7928cc8ea"
proposal2 = "https://snapshot.org/#/stgdao.eth/proposal/0x3cb9430062af89937887e9d359e4765de4f138c6bcea49ee66225a8fa998e97b"
proposal3 = "https://snapshot.org/#/stgdao.eth/proposal/0xf1274081c9f4db1db77f30f21b53f61dde8716f8d3f2aac7367709bd4af369b2"


data = pd.read_excel(data_path, engine='openpyxl', dtype={"Profile ID": str, "Password": str, "GTC Staking": str, "Gitcoin": str, "Twitter": str, "Discord": str,
                                                          "Google": str, "Github": str, "Facebook": str, "Linkedin": str, "ENS": str, "BrightID": str, "Proof of Humanity": str,
                                                          "ETH": str, "Snapshot": str, "GitPOAP": str, "NFT Holder": str, "ZkSync": str, "Lens": str, "Gnosis Safe": str, "Coinbase": str,
                                                          "Guild Membership and Roles": str, "Hypercerts": str, "PHI": str, "Holonym": str, "Idena": str, "Civic": str, "POINT": str})

data_login = pd.read_excel(data_path2, engine='openpyxl', dtype={"Twitter": str, "Twitter Password": str, "Discord": str,
                                                                 "Facebook Useragent": str, "Facebook Cookie": str})


start_idx = int(input("Enter the starting index of the profile range: ")) - 1
end_idx = int(input("Enter the ending index of the profile range: ")) - 1

def generate_password(length):
    if length < 4:
        print("Password length should be at least 4")
        return None

    all_characters = string.ascii_letters + string.digits + string.punctuation

    password = []
    password.append(random.choice(string.ascii_lowercase))  # Ensures at least one lowercase letter
    password.append(random.choice(string.ascii_uppercase))  # Ensures at least one uppercase letter
    password.append(random.choice(string.digits))  # Ensures at least one number
    password.append(random.choice(string.punctuation))  # Ensures at least one special character

    for i in range(length-4):  # Remaining characters can be anything
        password.append(random.choice(all_characters))

    random.shuffle(password)  # Shuffles the characters around

    return "".join(password)
def find_shadow_element_with_js(driver, css_selector):
    element = driver.execute_script(f'return document.querySelector("{css_selector}").shadowRoot')
    return element
def expand_shadow_element(driver, element):
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root
def setup_logger(logger_name):
    logger = colorlog.getLogger(logger_name)

    # Removes previous handlers, if they exist.
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "|%(log_color)s%(asctime)s| - Profile [%(name)s] - %(levelname)s - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
def click_if_exists(driver, locator):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, locator))
            )
            element.click()
            time.sleep(random.uniform(1.3, 2.1))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def input_text_if_exists(driver, locator, text):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            # Clearing the input field
            element.clear()
            # Write the new text into the field
            for character in text:
                element.send_keys(character)
                time.sleep(random.uniform(0.075, 0.124))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def scan_and_process_page(driver, data_path, profile_id, logger):
    results = {}  # create an empty dictionary to store our results
    time.sleep(10)
    try:
        # wait up to 10 seconds for the elements to become available
        titles = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h1.text-lg"))
        )
        buttons = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.verify-btn"))
        )
        if titles and buttons:   # only iterate if titles and buttons are not empty
            for title, button in zip(titles, buttons):
                # store the name of the title and button in our dictionary
                # we assume the button's text indicates whether the title is verified
                results[title.text] = button.text == 'Verified'
                time.sleep(random.uniform(0.09, 0.13))

    except TimeoutException:
        logger.warning("No stamps found for this account")

    finally:
        logger.info("Get all stamp data")

    # Load the existing dataframe
    data = pd.read_excel(data_path, engine='openpyxl', dtype={"Profile ID": str, "Password": str})

    # Find the index of the profile in the dataframe
    profile_index = data[data['Profile ID'] == profile_id].index[0]

    # Update the appropriate row with the new data
    for column, value in results.items():
        data.loc[profile_index, column] = value

    # Save the updated dataframe back to the Excel file
    data.to_excel(data_path, index=False)
def confirm_stamp(driver, logger):
    metamask_window_handle = find_metamask_notification(driver, logger)
    if metamask_window_handle:
        click_if_exists(driver, '/html/body/div[1]/div/div[2]/div/div[3]/button[2]')
        driver.switch_to.window(driver.window_handles[0])
        logger.info("Action is approve")
        return True
    else:
        driver.switch_to.window(driver.window_handles[0])
        logger.warning(f"MetaMask Notification window not found after 5 attempts")
        return False
def confirm_transaction(driver, logger):

    metamask_window_handle = find_metamask_notification(driver, logger)

    if metamask_window_handle:
        find_confirm_button_js = '''
        function findConfirmButton() {
          return document.querySelector('[data-testid="page-container-footer-next"]');
        }
        return findConfirmButton();
        '''
        confirm_button = driver.execute_script(find_confirm_button_js)

        if confirm_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
            for i in range(5):
                if metamask_window_handle not in driver.window_handles:
                    logger.info("Action is approve")
                    return True
                print(f"Click attempt {i + 1}")
                driver.execute_script("arguments[0].click();", confirm_button)
                time.sleep(3)
            logger.info("Action is approve")
            return True
        else:
            logger.warning("Confirm button not found")
            return False
    else:
        logger.warning(f"MetaMask Notification window not found after 5 attempts")
        return False
def metamask_login(driver, password):
    driver.get(metamask_url)
    input_text_if_exists(driver, '//*[@id="password"]', password)
    click_if_exists(driver, '//*[@id="app-content"]/div/div[3]/div/div/button')
    time.sleep(1.4)
    click_if_exists(driver, "/html/body/div[1]/div/div[1]/div/div[2]/div/div")
    time.sleep(1.4)
    click_if_exists(driver, "//*[contains(text(), 'Ethereum Mainnet')]")
    return True
def find_metamask_notification(driver, logger):
    metamask_window_handle = None

    for attempt in range(5):
        time.sleep(5)

        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'MetaMask Notification' in driver.title:
                metamask_window_handle = handle
                logger.info("MetaMask window found!")
                break

        if metamask_window_handle:
            break

    return metamask_window_handle
def connect_to_gitcoin(driver, logger, attempts=5, sleep_time=5):
    # Navigate to the Gitcoin website
    logger.info("Connecting to Gitcoin...")
    driver.get(Gitcoin)

    time.sleep(3)
    try:
        element = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[4]/div/section/footer/button[1]"))
            )
        metamask_window_handle = find_metamask_notification(driver, logger)
        if metamask_window_handle:
            click_if_exists(driver, '/html/body/div[1]/div/div[2]/div/div[3]/button[2]')
            driver.switch_to.window(driver.window_handles[0])
            logger.info("Re-confirm signature in wallet")
            return True
        else:
            logger.warning(f"MetaMask Notification window not found after {attempts} attempts")
            return False
    except TimeoutException:
        math = 1+5

    current_url = driver.current_url
    # Check if we're already on the dashboard page
    if 'https://passport.gitcoin.co/#/dashboard' in current_url:
        logger.info("Already connected to Gitcoin!")
        return True

    start_button = '/html/body/div[1]/div/div/div/div/div[2]/div/div/button'
    # Try to click the start button
    click_if_exists(driver, start_button)

    time.sleep(3)
    current_url = driver.current_url
    # Check if we're on the dashboard page after clicking the start button
    if 'https://passport.gitcoin.co/#/dashboard' in current_url:
        logger.info("Connected to Gitcoin after clicking the start button!")
        return True

    # Store a reference to the main document
    main_document = driver.switch_to.default_content

    try:
        # Try to select MetaMask as the wallet for a specified number of attempts
        for attempt in range(attempts):
            logger.info(f"Attempt to select MetaMask...")
            time.sleep(sleep_time)

            # Switch to the shadow root
            root1 = find_shadow_element_with_js(driver, 'body > onboard-v2')
            if root1 is not None:
                button = root1.find_element(By.CSS_SELECTOR,
                                            'section > div > div > div > div > div > div > div.content.flex.flex-column.svelte-b3j15j > div.scroll-container.svelte-b3j15j > div > div > div > div:nth-child(1) > button')
                # Switch back to the main document
                driver.switch_to.default_content = main_document

                if button is not None:
                    button.click()
                    logger.info("MetaMask selected!")
                    break
    except Exception:
        logger.error("Error with shadow root button")

    metamask_window_handle = find_metamask_notification(driver, logger)
    if metamask_window_handle:
        click_if_exists(driver, '/html/body/div[1]/div/div[2]/div/div[3]/div[2]/button[2]')
        click_if_exists(driver, "/html/body/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/footer/button[2]")
        try:
            confirm_stamp(driver, logger)
        except Exception:
            driver.switch_to.window(driver.window_handles[0])
            logger.info("Connection confirmed, you're connected to Gitcoin!")
            return True
        driver.switch_to.window(driver.window_handles[0])
        logger.info("Connection confirmed, you're connected to Gitcoin!")
        return True
    else:
        driver.switch_to.window(driver.window_handles[0])
        logger.error("MetaMask notification handle not found")
        return False
def login_to_twitter(driver, index, logger):
    # Start of the Twitter connection process
    logger.info("Twitter connection began...")
    # Navigate to the Twitter website
    driver.get("https://twitter.com/")

    try:
        # Look for an element that appears only when logged out (you can replace 'Placehold' with the correct name)
        # If this element is found, it means that we are not currently logged in
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[1]/div/div/div/div/div[1]/div"))
        )
        logger.info("Not logged in to Twitter, starting login process...")
        # Retrieve Twitter username and password from a data frame
        Twitter = data_login.loc[index, "Twitter"]
        Twitter_password = data_login.loc[index, "Twitter Password"]

        # Input username if the corresponding input field exists
        input_text_if_exists(driver, "/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[5]/label/div/div[2]/div/input", Twitter)
        # Click on the next button (or another button leading to the password input)
        click_if_exists(driver, "/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[6]")
        # Input password if the corresponding input field exists
        input_text_if_exists(driver, "/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input", Twitter_password)
        # Click on the login button
        click_if_exists(driver, "/html/body/div/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/div")

        # The following block seems to be designed for the purpose of changing the Twitter password
        # However, it's unclear where the Change_password variable comes from, so I'm leaving it as is
        if Change_password == 1:
            try:
                annoying_staff = "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[1]/div/div/div/div[1]/div"
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         annoying_staff))
                )
                # Click to close any pop-up or unnecessary interface elements
                click_if_exists(driver, annoying_staff)
                logger.info("Close annoying staff")
            except TimeoutException:
                # This math operation seems to do nothing, so it might be removed
                math = 1+2

            # The following actions appear to navigate through the Twitter interface to get to the password change option
            click_if_exists(driver, "/html/body/div[1]/div/div/div[2]/header/div/div/div/div[1]/div[2]/nav/div")
            # More navigation steps
            click_if_exists(driver, "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div[2]/div/div[3]/div/div/div/div/div[4]/div[3]")
            # More navigation steps
            click_if_exists(driver, "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div[2]/div/div[3]/div/div/div/div/div[4]/section/a[1]")
            # More navigation steps
            click_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div/section[2]/div[2]/div/div[3]/a")
            # Input the old password
            input_text_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div/section[2]/div[2]/div[1]/div[1]/label/div/div[2]/div/input", Twitter_password)
            # Generate a new password
            password = generate_password(32)
            # Update the password in the data frame and save it to an Excel file
            data_login.at[index, "Twitter Password"] = password
            data_login.to_excel(data_path2, index=False)
            # Log a warning about the password update
            logger.warning(f"Update you old password '{Twitter_password}' to this one '{password}'")
            # Input the new password
            input_text_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div/section[2]/div[2]/div[1]/div[3]/label/div/div[2]/div/input", password)
            # Confirm the new password
            input_text_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div/section[2]/div[2]/div[1]/div[4]/label/div/div[2]/div/input", password)
            # Submit the password change
            click_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div/section[2]/div[2]/div[3]/div")
            # Pause for a while to let the changes take effect
            time.sleep(2.3)
        else:
            logger.info("Done with twitter, go to Gitcoin page...")

    except TimeoutException:
        logger.info("Already logged in to Twitter.")

    # It's not clear what the dashboard variable refers to, so I'm leaving it as is
    driver.get(dashboard)
    # Clicking through some more interface elements
    click_if_exists(driver, "/html/body/div[1]/div/div/div/div/div[2]/div/div[3]/div/div[2]/button")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[1]/span")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[5]/button")

    # Switch to the last opened window
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)

    click_if_exists(driver, "/html/body/div[1]/div/div/div[2]/main/div/div/div[2]/div/div/div[1]/div[3]/div")
    time.sleep(5)
    confirm_stamp(driver, logger)
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[5]/button")
    logger.info("Done with connection, your Twitter account is now linked with this wallet!")
def discord_login(driver, index, logger):
    logger.info("Using magic JS skript to enter discord via token...")
    token = data_login.loc[index, "Discord"]


    driver.get("https://discord.com/")
    script = f"""
            const token = "{token}";
            setInterval(() => {{
                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
            }}, 50);
            setTimeout(() => {{
                location.reload();
            }}, 2500);
        """
    driver.execute_script(script)
    time.sleep(10)

    logger.info("Send token interaction moving to dashboard...")
    driver.get(dashboard)
    click_if_exists(driver, "/html/body/div[1]/div/div/div/div/div[2]/div/div[4]/div/div[2]/button")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[1]/span")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[3]/button")

    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)

    click_if_exists(driver, "/html/body/div[1]/div[2]/div[1]/div[1]/div/div/div/div/div/div[2]/button[2]")
    time.sleep(5)
    confirm_stamp(driver, logger)
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[3]/button")

    logger.info("Done with connection, you discord now is linked with this wallet!")
def facebook_login(driver, index, logger, options):
    # Retrieve user-agent and cookies for a particular profile from the data frame
    user_agent = data_login.loc[index, "Facebook Useragent"]
    cookies_str = data_login.loc[index, "Facebook Cookie"]

    # Convert JSON string to list of dictionaries
    cookies = json.loads(cookies_str)

    # Log the process of browser fingerprint changing
    logger.warning("Changing browser fingerprint to trick 'facebook.com'...")

    # Delete all old cookies
    driver.delete_all_cookies()

    # Set new user-agent
    options.add_argument(f'user-agent={user_agent}')

    # Navigate to the Facebook website
    driver.get("https://www.facebook.com/")

    # Log the process of injecting new cookie
    logger.warning("Injecting new cookie")

    # Add cookies
    for cookie in cookies:
        # Remove 'expirationDate' field as it may not be supported by WebDriver
        if 'expirationDate' in cookie:
            del cookie['expirationDate']
        driver.add_cookie(cookie)

    # Log the successful bypass of Facebook
    logger.info("Facebook was easily tricked, moving to dashboard...")

    # Refresh the page to ensure cookies are loaded
    driver.refresh()

    # Navigate to the dashboard (you need to define this 'dashboard' variable)
    driver.get(dashboard)

    # Click to start the Facebook connection process (you need to ensure these xpaths are correct)
    click_if_exists(driver, "/html/body/div[1]/div/div/div/div/div[2]/div/div[7]/div/div[2]/button")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[1]/span")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[4]/button")

    # Switch to the last opened window
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)

    # Complete the Facebook connection process (you need to ensure these xpaths are correct)
    click_if_exists(driver,
                    "/html/body/div[1]/div/div/div/div/div/div/div/div[1]/div[3]/div/div/div/div/div/div/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/div/div/div/div[1]")
    time.sleep(5)

    confirm_stamp(driver, logger)
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[4]/button")

    # Log the successful connection of the Facebook account with the wallet
    logger.info("Done with connection, your Facebook now is linked with this wallet!")
def vote(driver, logger, proposal):

    logger.info("Go to proposal page...")
    driver.get(proposal)

    element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div[2]/div[2]/div/div/div/div[2]/div[1]/div/button/span[2]")))
    if element.text == "Connect wallet":
        click_if_exists(driver, "/html/body/div[1]/div[1]/div[2]/div[2]/div/div/div/div[2]/button")
        click_if_exists(driver, "/html/body/div[2]/div/div[2]/div[2]/div/div/div[1]/button")

        metamask_window_handle = find_metamask_notification(driver, logger)

        if metamask_window_handle:
            Confirm_conection = '/html/body/div[1]/div/div[2]/div/div[3]/div[2]/button[2]'
            click_if_exists(driver, Confirm_conection)
            Confirm_conection2 = "/html/body/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/footer/button[2]"
            click_if_exists(driver, Confirm_conection2)
            driver.switch_to.window(driver.window_handles[0])
            logger.info("Connection confirmed, you're connected to Snapshot!")
        else:
            driver.switch_to.window(driver.window_handles[0])
            logger.error("MetaMask notification handle not found")
    else:
        logger.info("It appears you've already logged in before")

    yes = "//button[@data-testid='sc-choice-button-0']"  # 'Yes' button locator
    no = "//button[@data-testid='sc-choice-button-1']"  # 'No' button locator
    choices = [yes, no]
    random_choice = random.choice(choices)
    click_if_exists(driver, random_choice)
    vote_button = "//button[@data-testid='proposal-vote-button']"
    click_if_exists(driver, vote_button)
    try:
        gate = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.XPATH,
            "/html/body/div[2]/div/div[2]/div[1]/div/div/div[2]/div/div/div/a")))
        logger.info("It seems like you have 0 voting power, sad...")
        return False
    except TimeoutException:
        try:
            refresh_voting = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH,
                                             "/html/body/div[2]/div/div[2]/div[1]/div/div/div[1]/div[3]/span[2]/button")))
            refresh_voting.click()
        except TimeoutException:
            math3 = 22+6
        click_if_exists(driver, "/html/body/div[2]/div/div[2]/div[2]/div[2]/button")
        metamask_window_handle = find_metamask_notification(driver, logger)

        if metamask_window_handle:
            click_if_exists(driver, "/html/body/div[1]/div/div[2]/div/div[3]/div[1]")
            click_if_exists(driver, "/html/body/div[1]/div/div[2]/div/div[4]/button[2]")
            driver.switch_to.window(driver.window_handles[0])
            logger.info(f"Vote confirmed in wallet, waiting result...")
            try:
                end_button = WebDriverWait(driver, 33).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/div[2]/div/button[3]"))
                )
                end_button.click()
                logger.info("Find conformation on page!")
            except TimeoutException:
                logger.info("Dont find conformation, hope action was successful...")
        else:
            driver.switch_to.window(driver.window_handles[0])
            logger.error("MetaMask notification handle not found")
def snapshot_stamp(driver, logger):

    if vote(driver, logger, proposal1) is False:
        logger.error("Voting is failed, sad...")
        return
    vote(driver, logger, proposal2)
    vote(driver, logger, proposal3)

    driver.get(dashboard)

    click_if_exists(driver, "/html/body/div[1]/div/div/div/div/div[2]/div/div[13]/div/div[2]/button")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[1]/span")
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[4]/button")
    confirm_stamp(driver, logger)
    click_if_exists(driver, "/html/body/div[5]/div[2]/div[3]/div/div/div/div/div[4]/button")
    logger.info("Done, you obtain Snapshot stamp")
def process_profile(idx):
    # Retrieving profile ID and password from data at the specific index
    profile_id = data.loc[idx, "Profile ID"]
    password = data.loc[idx, "Password"]

    # Setup logger for tracking actions
    logger = setup_logger(f'{idx + 1}')
    logger.info(f"Processing profile...")

    # Start browser profile using localhost
    req_url = f'http://localhost:3001/v1.0/browser_profiles/{profile_id}/start?automation=1'
    response = requests.get(req_url)
    response_json = response.json()
    logger.info(f"Browser profile started, processing response...")

    # Setting port for automation
    port = str(response_json['automation']['port'])

    # Setup options for Chrome browser
    options = webdriver.ChromeOptions()
    options.debugger_address = f'127.0.0.1:{port}'

    # Setup WebDriver service for Chrome
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    logger.info(f"Chrome WebDriver setup successful...")

    # Manipulating tabs in the browser
    # Open a new tab
    driver.execute_script("window.open('about:blank', 'tab2');")
    driver.switch_to.window("tab2")
    initial_window_handle = driver.current_window_handle  # The new empty tab is now the initial tab

    # Close all other tabs
    for handle in driver.window_handles:
        if handle != initial_window_handle:
            driver.switch_to.window(handle)
            logger.info("Cleaning up the tabs...")
            driver.close()

    # Switch back to the initial tab
    driver.switch_to.window(initial_window_handle)
    driver.get(metamask_url)

    # Attempt to login to Metamask
    try:
        result = metamask_login(driver, password)
        if result is True:
            logger.info(f"Metamask gate passed")
        elif result is False:
            logger.warning("Something went wrong during Metamask extension login")
    except Exception:
        logger.error("Unexpected error during Metamask extension login, manual check recommended")

    # Attempt to connect to Gitcoin
    try:
        result = connect_to_gitcoin(driver, logger, attempts=5, sleep_time=5)
        if result is True:
            logger.info(f"Gitcoin gate passed")
        elif result is False:
            logger.warning("It appears you've already logged in before, or it may be mistake")
    except Exception:
        logger.error("Unexpected error during Gitcoin connection, manual check recommended")

    # Check if on Gitcoin welcome page
    current_url = driver.current_url
    if 'https://passport.gitcoin.co/#/welcome' in current_url:
        # If on welcome page, refresh and skip unnecessary steps
        driver.refresh()
        skip_button = '//*[@id="__next"]/div/div/div/div/div[2]/div/div/div[3]/div/div[2]/button'
        click_if_exists(driver, skip_button)
        time.sleep(3)
        click_if_exists(driver, skip_button)
        time.sleep(3)
        click_if_exists(driver, '//*[@id="__next"]/div/div/div/div/div[2]/div/div/div[3]/div/div[2]/button[2]')
        logger.info("Navigating through the welcome page")

        # Attempt to confirm stamp if present
        try:
            stamp_button = "/html/body/div[5]/div[4]/div/section/div/div[1]/div/div[4]/button[2]"
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, stamp_button)))
            logger.info("Found stamp, attempting to confirm in wallet...")
            click_if_exists(driver, "/html/body/div[5]/div[4]/div/section/div/div[2]/button")
            click_if_exists(driver, stamp_button)
            confirm_stamp(driver, logger)
        except TimeoutException:
            # If no stamp found, move to dashboard
            logger.warning("No stamp found, moving to dashboard")
            click_if_exists(driver, "/html/body/div[5]/div[4]/div/section/div/div[2]/button")
            click_if_exists(driver, '/html/body/div[5]/div[4]/div/section/div/div[1]/div/button')

    # Perform scanning and processing of the page
    scan_and_process_page(driver, data_path, profile_id, logger)
    logger.info("Page scanning and processing completed")
    function_mapping = {
        "Twitter": {"func": login_to_twitter, "args": (driver, idx, logger)},
        "Discord": {"func": discord_login, "args": (driver, idx, logger)},
        "Snapshot": {"func": snapshot_stamp, "args": (driver, logger)},
        "Facebook": {"func": facebook_login, "args": (driver, idx, logger, options)},
    }
    # Get a row for a specific account
    row = data[data['Profile ID'] == profile_id].iloc[0]
    bro = 0
    # Iterate over the columns in the row
    for column in data.columns:
        # If the value is True, call the corresponding function
        if row[column] == "0" and column in function_mapping:
            function_data = function_mapping[column]
            function = function_data["func"]
            args = function_data["args"]
            function(*args)
            bro = 1
    if bro == 0:
        logger.warning("All possible verification is done!")
    # Tip - You can delete 'mapping' system and run any verification type alone.
    # login_to_twitter(driver, idx, logger)
    driver.get("https://www.wikipedia.org/")
    logger.info("Place a filler to avoid long loading during future run")
    driver.close()
    logger.info("WebDriver closed")

with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Adjust max_workers as needed
    # Submit tasks to executor
    for idx in range(start_idx, end_idx + 1):
        futures = {executor.submit(process_profile, idx): idx}
        time.sleep(20)

    # Collect results as they become available
    for future in concurrent.futures.as_completed(futures):
        idx = futures[future]
        try:
            future.result()
        except Exception:
            print("Something go wrong...")