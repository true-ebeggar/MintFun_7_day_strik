# Standard library imports
import sys
import time
import random
import datetime
import os

# Third-party imports
import pandas as pd
import requests
import json

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
import colorlog
import logging
from colorama import init, Fore


if not os.path.isfile('config_user.json'):

    print("You need to set parameter, they can be change any time in 'config_user' file")
    print("New skript need you metamask identificator, it look like this:")
    print("chrome-extension://hpbbepbnmcaoajhapnmjfjakmaacabni/home.html#")
    print("You need only this parth 'hpbbepbnmcaoajhapnmjfjakmaacabni'")
    IDENTIFICATOR = input("Enter you personal MetaMask identificator: ")
    MIN_DELAY = input("Enter minimal delay between action: ")
    MAX_DELAY = input("Enter maximal delay between action: ")
    config_user = {
        'IDENTIFICATOR': IDENTIFICATOR,
        'MIN_DELAY': MIN_DELAY,
        'MAX_DELAY': MAX_DELAY,
    }

    with open('config_user.json', 'w') as f:
        json.dump(config_user, f)

    print("Configuration saved successfully.")
else:
    print("Configuration file already exists, it can be change any time in 'config_user' file")

with open('config_user.json', 'r') as f:
    config_user = json.load(f)


IDENTIFICATOR = str(config_user['IDENTIFICATOR'])
MIN_DELAY = int(config_user['MIN_DELAY'])
MAX_DELAY = int(config_user['MAX_DELAY'])
METAMASK_URL = f"chrome-extension://{IDENTIFICATOR}/home.html#"
DATA_PATH = "Data.xlsx"

# Load data
df = pd.read_excel(DATA_PATH)
df.index = range(1, len(df) + 1)

# Retrieve profiles and passwords
profiles = df['Profile ID'].tolist()
passwords = df['Password'].tolist()

def update_excel_with_timestamp(idx, file_path, df, logger):
    """
    Updates the timestamp in the provided dataframe and saves it to an excel file.

    Args:
    - idx (int): Index of the profile.
    - file_path (str): Path to the excel file.
    - df (pd.DataFrame): The data frame containing profile data.
    - logger (logging.Logger): Configured logger instance.

    Returns:
    None
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx, 'Time_Stamp'] = timestamp
        df.to_excel(file_path, index=False)
        logger.info(f"Timestamp updated for ID {idx} to {timestamp}")
    except Exception as e:
        logger.error(f"Error updating timestamp for ID {idx}: {e}")
def get_time_difference_in_hours(idx, df, logger):
    """
    Calculates the time difference in hours between the current time and the last transaction time.

    Args:
    - idx (int): Index of the profile.
    - df (pd.DataFrame): The data frame containing profile data.
    - logger (logging.Logger): Configured logger instance.

    Returns:
    - float: Time difference in hours. Returns 99999 in case of an error.
    """
    try:
        timestamp_str = str(df.at[idx, 'Time_Stamp'])
        last_transaction_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        time_difference = current_time - last_transaction_time
        hours_passed = time_difference.total_seconds() / 3600
        logger.info(f"Time difference for ID {idx}: {hours_passed:.2f} hours")
        return hours_passed
    except Exception as e:
        logger.error(f"Error reading timestamp for ID {idx}: {e}")
        return 99999
def check_max_trx_reached(df, max_trx):
    """
    Checks if the maximum number of transactions has been reached for all profiles.

    Args:
    - df (pd.DataFrame): The data frame containing profile data.
    - max_trx (int): Maximum number of transactions.

    Returns:
    - bool: True if maximum transactions reached, False otherwise.
    """
    for value in df['Mint_total']:
        if value < max_trx:
            return False
    return True
def SetupGayLogger(logger_name):
    """
    SetupGayLogger initializes a colorful logging mechanism, presenting each log message in a beautiful
    rainbow sequence. The function accepts a logger name and returns a logger instance that can be used
    for logging messages.

    Parameters:
    - logger_name (str): A name for the logger.

    Returns:
    - logger (Logger): A configured logger instance.
    """

    # Initialize the colorama library, which provides an interface for producing colored terminal text.
    init()

    def rainbow_colorize(text):
        """
        Transforms a given text into a sequence of rainbow colors.

        Parameters:
        - text (str): The text to be colorized.

        Returns:
        - str: The rainbow colorized text.
        """
        # Define the sequence of colors to be used.
        colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
        colored_message = ''

        # For each character in the text, assign a color from the sequence.
        for index, char in enumerate(text):
            color = colors[index % len(colors)]
            colored_message += color + char

        # Return the colorized text and reset the color.
        return colored_message

    class RainbowColoredFormatter(colorlog.ColoredFormatter):
        """
        Custom logging formatter class that extends the ColoredFormatter from the colorlog library.
        This formatter first applies rainbow colorization to the entire log message before using the
        standard level-based coloring.
        """

        def format(self, record):
            """
            Format the log record. Overridden from the base class to apply rainbow colorization.

            Parameters:
            - record (LogRecord): The log record.

            Returns:
            - str: The formatted log message.
            """
            # First rainbow colorize the entire message.
            message = super().format(record)
            rainbow_message = rainbow_colorize(message)
            return rainbow_message

    # Obtain an instance of a logger for the provided name.
    logger = colorlog.getLogger(logger_name)

    # Ensure that if there are any pre-existing handlers attached to this logger, they are removed.
    # This prevents duplicate messages from being displayed.
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    # Create a stream handler to output log messages to the console.
    handler = colorlog.StreamHandler()

    # Assign the custom formatter to the handler.
    handler.setFormatter(
        RainbowColoredFormatter(
            "|%(log_color)s%(asctime)s| - Profile [%(name)s] - %(levelname)s - %(message)s",
            datefmt=None,
            reset=False,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
    )

    # Attach the handler to the logger.
    logger.addHandler(handler)

    # Set the minimum logging level to DEBUG. This means messages of level DEBUG and above will be processed.
    logger.setLevel(logging.DEBUG)

    return logger
def click_if_exists(driver, locator):
    """
    Tries to find and click an element on the web page using its XPATH locator.
    """
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
            logger = SetupGayLogger("Emergency massage")
            logger.warning("Element became stale. Retrying...")
            attempts += 1
            time.sleep(3)
    return False
def confirm_transaction(driver, logger):
    """
    Sets gas values and confirms a transaction on the MetaMask extension.
    """
    metamask_window_handle = find_metamask_notification(driver, logger)

    if metamask_window_handle:
        logger.info("Setting gas values in MetaMask.")
        click_if_exists(driver, '//*[@id="app-content"]/div/div[2]/div/div[5]/div[2]/div/div/div/div[1]/button')
        click_if_exists(driver, '//*[@id="popover-content"]/div/div/section/div[2]/div/div[2]/div[1]/button')
        gas = f"{random.uniform(0.005, 0.05):.5f}".replace(".", ",")
        input_text_if_exists(driver, '//*[@id="popover-content"]/div/div/section/div[2]/div/div[2]/div[1]/div[3]/div[2]/label/div[2]/input', gas)
        input_text_if_exists(driver, '//*[@id="popover-content"]/div/div/section/div[2]/div/div[2]/div[1]/div[3]/div[3]/label/div[2]/input', gas)
        click_if_exists(driver, '//*[@id="popover-content"]/div/div/section/div[3]/button')
        logger.info("Gas values set successfully.")

        find_confirm_button_js = '''
        function findConfirmButton() {
          return document.querySelector('[data-testid="page-container-footer-next"]');
        }
        return findConfirmButton();
        '''
        confirm_button = driver.execute_script(find_confirm_button_js)

        if confirm_button:
            for i in range(5):
                if metamask_window_handle not in driver.window_handles:
                    logger.info("Transaction approved successfully!")
                    return True
                logger.info(f"Attempting to click the confirm button ({i + 1}/5)...")
                driver.execute_script("arguments[0].click();", confirm_button)
                time.sleep(3)
            return True
        else:
            logger.warning("Unable to find the 'Confirm' button in MetaMask.")
            return False
    else:
        logger.warning(f"MetaMask Notification window not found after 5 attempts.")
        return False
def input_text_if_exists(driver, locator, text):
    """
    Tries to find an input field on the web page and enters the provided text into it.
    """
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            element.clear()  # Clearing any existing text in the input field
            # Typing the provided text character by character
            for character in text:
                element.send_keys(character)
                time.sleep(random.uniform(0.075, 0.124))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            logger = SetupGayLogger("Emergency massage")
            logger.warning("Input element became stale. Retrying...")
            attempts += 1
            time.sleep(3)
    return False
def find_metamask_notification(driver, logger):
    """
    Searches for the MetaMask Notification window among the open browser windows.
    """
    metamask_window_handle = None

    for attempt in range(5):
        time.sleep(5)

        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'MetaMask Notification' in driver.title:
                metamask_window_handle = handle
                logger.info("Found the MetaMask Notification window!")
                break

        if metamask_window_handle:
            break

    return metamask_window_handle


def process_profile(idx, nugger):
    # Extracting profile details from pre-defined lists.
    profile_id = profiles[idx]
    password = passwords[idx]

    # Starting a browser session with the extracted profile ID.
    open_url = f"http://local.adspower.net:50325/api/v1/browser/start?user_id={profile_id}"
    resp = requests.get(open_url).json()

    # If there's an error starting the browser, notify and exit the script.
    if resp["code"] != 0:
        nugger.error(resp["msg"])
        nugger.error("Failed to start a driver")
        sys.exit()

    # Set up and start a Chrome browser with given configurations.
    chrome_driver = resp["data"]["webdriver"]
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", resp["data"]["ws"]["selenium"])
    driver = webdriver.Chrome(service=Service(chrome_driver), options=chrome_options)

    # Memorize the primary browser window.
    initial_window_handle = driver.current_window_handle
    time.sleep(1.337)  # Wait for a short while.

    # Close any additional browser tabs.
    for tab in driver.window_handles:
        if tab != initial_window_handle:
            driver.switch_to.window(tab)
            nugger.info("Cleaning extra tabs...")
            driver.close()

    # Go back to the primary browser window.
    driver.switch_to.window(initial_window_handle)
    try:
        # Access MetaMask and input the password.
        driver.get(METAMASK_URL)
        input_text_if_exists(driver, '//*[@id="password"]', password)
        # Progress through MetaMask prompts.
        click_if_exists(driver, '//*[@id="app-content"]/div/div[3]/div/div/button')
        time.sleep(5)
        click_if_exists(driver, '//*[@id="app-content"]/div/div[1]/div/div[2]/div/div')
        click_if_exists(driver, "//*[contains(text(), 'Ethereum Mainnet')]")
        nugger.info("Logged into the wallet, switched to 'ETH' mainnet")

        # Navigate to mint.fun trending feed.
        driver.get("https://mint.fun/feed/trending")
        time.sleep(5)

        # Check if there's a need to connect the wallet and handle it.
        element = driver.find_element(By.XPATH, '//*[@id="__next"]/div[3]/div/nav/div/div/div/button/span')
        text = element.text
        if text == "Connect Wallet":
            click_if_exists(driver, '//*[@id="__next"]/div[3]/div/nav/div/div/div/button')
            click_if_exists(driver,
                            '//*[@id="__CONNECTKIT__"]/div/div/div/div[2]/div[2]/div[4]/div/div/div/div[1]/button[1]')

            # Manage MetaMask pop-up notifications.
            metamask_window_handle = find_metamask_notification(driver, nugger)
            if metamask_window_handle:
                # Interact with the MetaMask pop-up.
                click_if_exists(driver, '//*[@id="app-content"]/div/div[2]/div/div[3]/div[2]/button[2]')
                click_if_exists(driver, '//*[@id="app-content"]/div/div[2]/div/div[2]/div[2]/div[2]/footer/button[2]')
                try:
                    click_if_exists(driver, '//*[@id="app-content"]/div/div[2]/div/div[2]/div[3]/button[2]')
                    click_if_exists(driver, '//*[@id="app-content"]/div/div[2]/div/div[2]/div[2]/button[2]')
                except Exception:
                    math = 2 - 4
                driver.switch_to.window(initial_window_handle)
            else:
                driver.switch_to.window(initial_window_handle)
                nugger.warning("Metamask pop-up not found. System might be overloaded.")
            nugger.info("Connected to the 'Element' page...")
        else:
            nugger.info("Already logged in. Skipping connection step.")

        # Switching to the Zora network in MetaMask.
        driver.get(METAMASK_URL)

        # Navigate to the MetaMask network selection dropdown.
        click_if_exists(driver, '//*[@id="app-content"]/div/div[1]/div/div[2]/div/div')
        try:
            # Wait for the interface to load before proceeding.
            time.sleep(5)

            # Attempt to select 'Zora' from the network dropdown list.
            element = driver.find_element(By.XPATH, "//*[contains(text(), 'Zora')]")
            element.click()

            # Log a message indicating the switch to Zora network.
            nugger.info("Switched to the Zora network.")

        except NoSuchElementException:
            click_if_exists(driver, "//*[contains(text(), 'Ethereum Mainnet')]")
            # If 'Zora' is not found in the dropdown, it means the network is not added.
            # Log a message to indicate the missing network.
            nugger.info("Zora network isn't added. Setting it up now.")

            # Navigate to MetaMask's "Add Network" settings page.
            driver.get(f"chrome-extension://{IDENTIFICATOR}/home.html#settings/networks/add-network")

            # Input required network details to add 'Zora'.
            # These details include Network Name, New RPC URL, Chain ID, Symbol, and Block Explorer URL.
            input_text_if_exists(driver,
                                 '//*[@id="app-content"]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/label/input',
                                 "Zora")
            input_text_if_exists(driver,
                                 '//*[@id="app-content"]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/label/input',
                                 "https://rpc.zora.energy/")
            input_text_if_exists(driver,
                                 '//*[@id="app-content"]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[3]/label/input',
                                 "7777777")
            input_text_if_exists(driver,
                                 '//*[@id="app-content"]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[4]/label/input',
                                 "ETH")
            input_text_if_exists(driver,
                                 '//*[@id="app-content"]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[5]/label/input',
                                 "https://explorer.zora.energy/")

            # Wait and confirm the network addition.
            time.sleep(2)
            click_if_exists(driver, '/html/body/div[1]/div/div[3]/div/div[2]/div[2]/div/div[2]/div/div[3]/button[2]')

        # Navigate to the free Zora NFTs page.
        nugger.info("Accessing free Zora NFTs page...")
        driver.get("https://mint.fun/feed/free?chain=zora")

        # Scroll down to load all available NFTs.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        # Fetch all the available NFT blocks.
        blocks = driver.find_elements(By.XPATH, '//*[@id="__next"]/div[3]/div/main/div/div[2]/div[3]/div')

        # Extract links from each block, representing individual NFTs.
        all_links = []
        for block in blocks:
            link_xpath = './div/div[2]/div[1]/div[1]/div/span/a'
            links = block.find_elements(By.XPATH, link_xpath)
            for link in links:
                link_url = link.get_attribute('href')
                all_links.append(link_url)

        # Log how many free NFTs were found.
        nugger.info(f"Identified {len(all_links)} NFTs available for minting.")

        # Randomly select an NFT to mint.
        selected_link = random.choice(all_links)
        nugger.info(f"Proceeding with this collection: {selected_link}")

        # Navigate to the chosen NFT's page.
        driver.get(selected_link)
        time.sleep(3)
        click_if_exists(driver, '//*[@id="__next"]/div[3]/div/main/div/div[2]/div[2]/div[3]/div[1]/button')

        # Confirm the transaction in MetaMask.
        confirm_transaction(driver, nugger)
        driver.switch_to.window(initial_window_handle)
        nugger.info("Transaction sent. Waiting for minting confirmation...")

        # Check the result of the minting process.
        try:
            time.sleep(10)
            # Wait for the confirmation message.
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[2]/div/div/div/div/div[1]'))
            )
            element_text = element.text

            # If successful, log a success message.
            if "successful" in element_text.lower():
                nugger.info("Minting was successful!")
                driver.close()
                return 1
            else:
                # If the status is unclear, log an ambiguous message.
                nugger.error(f"Uncertain minting outcome: {element_text}")
        except TimeoutException:
            # If it takes too long, suggest a manual check.
            nugger.error("Transaction took too long. Recommend checking manually.")
    finally:
        try:
            driver.close()
        except selenium.common.exceptions.InvalidSessionIdException:
            math = 1 - 4


# Input the range of indices for accounts.
start_idx = int(input("Enter the starting index: "))
end_idx = int(input("Enter the ending index: "))
sleep_delay = 300
# Validate the provided indices.
if start_idx > end_idx or start_idx < 1:
    print("Invalid input!")
    exit(1)

# Infinite loop to continuously mint for eligible accounts.
while True:
    # Generate and shuffle account indices within the specified range.
    indices = list(range(start_idx, end_idx + 1))
    random.shuffle(indices)
    eligible_id_found = False

    for idx in indices:
        # Initialize logger for the current index/account.
        nugger = SetupGayLogger(f'Account {idx}')
        total_trx = df.at[idx, 'Mint_total']
        nugger.info("You definitely should subscribe) 'https://t.me/CryptoBub_ble'")

        # Check if the account has already minted 7 times.
        if total_trx >= 7:
            nugger.info(f"Account {idx} has already minted 7 times. Skipping...")
            continue

        # Check if it's been less than 24 hours since the last mint for this account.
        if get_time_difference_in_hours(idx, df, nugger) < 24:
            nugger.info(f"Less than 24 hours since last mint for Account {idx}. Skipping...")
            continue

        # Check if all accounts have reached the max transaction limit.
        if check_max_trx_reached(df, 7):
            nugger.error("Max transactions reached for all accounts. Stopping process...")
            break

        eligible_id_found = True
        sleep_delay = 10
        try:
            result = process_profile(idx - 1, nugger)  # Adjusting for zero-based indexing
        except Exception:
            nugger.error(f"Error processing Account {idx}")
            continue

        # If minting was successful, update the records.
        if result == 1:
            df.at[idx, 'Mint_total'] += 1
            update_excel_with_timestamp(idx, DATA_PATH, df, nugger)
            wait_duration = random.uniform(MIN_DELAY, MAX_DELAY)
            nugger.info(f"Successful mint for Account {idx}. Waiting {wait_duration} seconds before next operation.")
            time.sleep(wait_duration)

    # If no eligible account was found, increase the wait duration.
    if not eligible_id_found:
        sleep_delay = sleep_delay * 1.5
        nugger.info(f"No eligible accounts found. Waiting {sleep_delay} seconds before checking again...")
        time.sleep(sleep_delay)
