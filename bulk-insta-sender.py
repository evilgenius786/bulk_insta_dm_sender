import csv
import os
import os.path
import time
import traceback

import instaloader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

t = 1
timeout = 5
wait = 3
uname = input("Please enter Instagram username: ")
pwd = input("Please enter Instagram password: ")
debug = False

headless = False
images = False
max = False
incognito = True
insta = "https://www.instagram.com"


def main():
    try:
        with open('users.txt') as ufile:
            oldusers = ufile.read().splitlines()
    except:
        oldusers = []
    try:
        with open('sent.txt') as sfile:
            sent = sfile.read().splitlines()
    except:
        sent = []
    choice = input("Enter 1 to scrape usernames from post, 2 to send them messages: ")
    if choice == "1":
        sessions = loadSessions()
        purl = input("Enter post URL: ").split("/")[-1]
        sindex = 1
        L, sindex = getIG(sessions, sindex)
        users = []
        try:
            post = instaloader.Post.from_shortcode(L.context, purl)
            for comment in post.get_comments():
                user = comment.owner.username
                if user not in oldusers:
                    print(user)
                    users.append(user)
            with open('users.txt', 'a') as ufile:
                ufile.write("\n".join(users))
        except:
            traceback.print_exc()
    elif choice == "2":
        driver = getChromeDriver()
        # driver.get('http://lumtest.com/myip.json')
        time.sleep(1)
        driver.get(f"{insta}/accounts/login/")
        # time.sleep(2)
        if "login" in driver.current_url:
            sendkeys(driver, '//input[@name="username"]', uname)
            sendkeys(driver, '//input[@name="password"]', pwd)
            click(driver, '//button[@type="submit"]')
        for user in oldusers:
            if user not in sent:
                driver.get(f"{insta}/{user}")
                print("Processing", user)
                try:
                    click(driver, '//button[text()="Follow"]')
                    print(f"Followed {user}")
                except:
                    print(f"Already followed {user}")
                name = getElement(driver, '//div/h1').text
                try:
                    click(driver, '//div[contains(text(),"Message")]')
                    msg = f'H! {name}\n'
                    sendkeys(driver, '//textarea[@placeholder="Message..."]', msg, True)
                    click(driver, '//button[text()="Send"]')
                    print(f"Sent msg to {user}", msg)
                    with open('sent.txt', 'a') as sfile:
                        sfile.write(user + "\n")
                    sent.append(user)
                    time.sleep(wait)
                except:
                    print("Account is private.")
            else:
                print(f"Message already sent to {user}")
    input("Done")


def getIG(sessions, sindex):
    print("Switching account...")
    user = sessions[sindex % len(sessions)]
    try:
        L = instaloader.Instaloader()
        L.load_session_from_file(username=user, filename=f"./sessions/{user}")
        return L, sindex + 1
    except Exception as e:
        print("getIG: Error", user, e)
        os.remove(user)
        return getIG(sessions, sindex + 1)


def write(file, lines):
    with open(file, mode='w', newline="", encoding="utf8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(lines)


def read(file):
    lines = []
    with open(file, mode='r', encoding="utf8") as f:
        reader = csv.reader(f)
        for line in reader:
            lines.append(line)
    return lines


def loadSessions():
    sessions = [line for line in os.listdir("./sessions/") if line[0] != "."]
    if len(sessions) == 0:
        createSession()
    return [line for line in os.listdir("./sessions/") if line[0] != "."]


def createSession():
    try:
        L = instaloader.Instaloader()
        print(f"Creating session for {uname}")
        L.login(uname, pwd)
        L.save_session_to_file(f"./sessions/{uname}")
        L.close()
    except Exception as e:
        print("createSession: Error", uname, e)


def click(driver, xpath, js=False):
    if js:
        driver.execute_script("arguments[0].click();", getElement(driver, xpath))
    else:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def getElement(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


def sendkeys(driver, xpath, keys, js=False):
    if js:
        JS_ADD_TEXT_TO_INPUT = """
          var elm = arguments[0], txt = arguments[1];
          elm.value += txt;
          elm.dispatchEvent(new Event('change'));
          """
        driver.execute_script(JS_ADD_TEXT_TO_INPUT, getElement(driver, xpath), keys)
        getElement(driver, xpath).send_keys(" \n")
        # driver.execute_script(f"arguments[0].value='{keys}';", getElement(driver, xpath))
    else:
        getElement(driver, xpath).send_keys(keys)


def getChromeDriver(proxy=None):
    options = webdriver.ChromeOptions()
    if debug:
        # print("Connecting existing Chrome for debugging...")
        options.debugger_address = "127.0.0.1:9222"
    else:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
    if not images:
        # print("Turning off images to save bandwidth")
        options.add_argument("--blink-settings=imagesEnabled=false")
    if headless:
        # print("Going headless")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    if max:
        # print("Maximizing Chrome ")
        options.add_argument("--start-maximized")
    if proxy:
        # print(f"Adding proxy: {proxy}")
        options.add_argument(f"--proxy-server={proxy}")
    if incognito:
        # print("Going incognito")
        options.add_argument("--incognito")
    return webdriver.Chrome(options=options)


def getFirefoxDriver():
    options = webdriver.FirefoxOptions()
    if not images:
        # print("Turning off images to save bandwidth")
        options.set_preference("permissions.default.image", 2)
    if incognito:
        # print("Enabling incognito mode")
        options.set_preference("browser.privatebrowsing.autostart", True)
    if headless:
        # print("Hiding Firefox")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(options)


def logo():
    print("""
.___                  __                                       
|   | _____   _______/  |______     ________________    _____  
|   |/     \ /  ___/\   __\__  \   / ___\_  __ \__  \  /     \ 
|   |  Y Y  \\\\___ \  |  |  / __ \_/ /_/  >  | \// __ \|  Y Y  \\
|___|__|_|  /____  > |__| (____  /\___  /|__|  (____  /__|_|  /
          \/     \/            \//_____/            \/      \/ 
===================================================================
             Bulk instagram DM sender from post URL
           Developed by www.fiverr.com/muhammadhassan7
       Presented to you by: https://creativebeartech.com/
===================================================================
""")


if __name__ == "__main__":
    main()
