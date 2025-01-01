from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os
import re

# load login creds
if not load_dotenv():
    print("Failed to load environment variables via .env")

USERNAME = os.getenv("USERNAME")
if not USERNAME:
    raise Exception("Failed to retrieve username from .env")
ENCRYPTED_PASSWORD = os.getenv("PASSWORD")
if not ENCRYPTED_PASSWORD:
    raise Exception("Failed to retrieve encrypted password from .env")
DECRYPT_KEY = os.getenv("DECRYPT_KEY")
if not DECRYPT_KEY:
    raise Exception("Failed to retrieve decrypt key from .env")

fernet = Fernet(DECRYPT_KEY)
PASSWORD = fernet.decrypt(ENCRYPTED_PASSWORD.encode()).decode()

WEBSITE_URL = "https://access.caltech.edu/tqfr/reports/list_surveys"

driver = webdriver.Chrome()

try:
    driver.get(WEBSITE_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_field = driver.find_element(By.NAME, "username")
    username_field.send_keys(USERNAME)

    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(PASSWORD)

    login_button = driver.find_element(By.NAME, "Sign In")
    login_button.click()
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "questiondiv"))
    )

    print("Logged into TQFR.")

except TimeoutException:
    print("Failed to log in. An element took too long to load.")

TQFR_HOME_URL = driver.current_url
RELEVANT_TERMS = [
    "FA 2023-24",
    "WI 2023-24",
    "SP 2023-24",
    "FA 2022-23",
    "WI 2022-23",
    "SP 2022-23",
]
RELEVANT_DIVS = ["EAS", "PMA"]

for term in RELEVANT_TERMS:
    try:
        # wait for table of divisions to load
        driver.find_element(By.LINK_TEXT, term).click()
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tablediv"))
        )

        TERM_URL = driver.current_url
        for division in RELEVANT_DIVS:
            # wait for table of departments to load
            division_link = driver.find_element(By.LINK_TEXT, division)
            division_link.click()
            WebDriverWait(driver, 3).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, "questiondiv"), "Department"
                )
            )

            DIVISION_URL = driver.current_url
            dept_divs = driver.find_elements(By.CLASS_NAME, "questiondiv")
            dept_links = []
            for div in dept_divs:
                # collect all links (can't click because stale element)
                try:
                    dept = div.find_element(By.TAG_NAME, "a").get_attribute("text")
                    if not dept:
                        continue
                    print(dept)
                    dept_links.append(
                        (
                            dept,
                            div.find_element(By.TAG_NAME, "a").get_attribute("href"),
                        )
                    )
                except NoSuchElementException:
                    pass

            for dept, link in dept_links:
                driver.get(link)
                WebDriverWait(driver, 3).until(
                    EC.text_to_be_present_in_element(
                        (By.CLASS_NAME, "questiondiv"), "Offering"
                    )
                )

                course_divs = driver.find_elements(By.CLASS_NAME, "questiondiv")
                course_links = []
                for div in course_divs:
                    # collect links for each course
                    try:
                        course_name = div.find_element(By.TAG_NAME, "a").get_attribute(
                            "text"
                        )
                        if not course_name:
                            continue

                        course_id = re.sub(
                            r"\b0+(?!\b)",
                            "",
                            course_name.lower().replace("/", "").replace(" ", "-"),
                        )
                        course_id = re.sub(r"(\d+)(?!$)(?!\d)", r"\1-", course_id)
                        print(course_id)

                        course_links.append(
                            (
                                course_id,
                                div.find_element(By.TAG_NAME, "a").get_attribute(
                                    "href"
                                ),
                            )
                        )
                    except NoSuchElementException:
                        pass

                for course_id, link in course_links:
                    save_path = os.path.join("html", "tqfr", term, division, dept)
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    filename = f"{course_id}.html"

                    driver.get(link)
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "survey_title"))
                    )

                    with open(
                        os.path.join(save_path, filename), "w", encoding="utf-8"
                    ) as f:
                        f.write(driver.page_source)

            # go back to term page
            driver.get(TERM_URL)
            WebDriverWait(driver, 3).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, "questiondiv"), "Division"
                )
            )

    except TimeoutException:
        print(f"Failed to scrape TQFRs for {term} (timed out).")

    driver.get(TQFR_HOME_URL)
