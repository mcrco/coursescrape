import re
import os
import json
from tqdm import tqdm
from collections import defaultdict
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet


def scrape(html, id):
    soup = BeautifulSoup(html, "html.parser")

    headers = soup.find_all("h1")
    title, course_name = headers[0], headers[1].text.strip()
    course_id = re.sub(r"\b0+(\d+)", r"\1", title.text.strip().split(" — ")[1])
    data = {"id": id, "course_id": course_id, "name": course_name}

    for section in soup.find_all("h2", class_="survey_report"):
        if "Instructor Section" in section.text or "Teaching Assistant" in section.text:
            if "instructor" not in data:
                data["instructor"] = defaultdict(dict)

            instructor_name = section.text.split(":")[-1].strip()
            data["instructor"][instructor_name]["type"] = (
                "Instructor"
                if "Instructor Section" in section.text
                else "Teaching Assistant"
            )
            tables = []
            sibling = section.find_next_sibling()
            while sibling and sibling.name != "h2":
                if sibling.name == "table":
                    tables.append(sibling)
                sibling = sibling.find_next_sibling()

            for table in tables:
                for row in table.find_all("tr")[1:]:
                    question = row.find("td", class_="questiondiv").text.strip()
                    scores = row.find_all("td", class_="celldiv")
                    score = scores[1].strong.text.strip()
                    stdev = scores[1].contents[2].text[2:].strip()
                    dept_avg = scores[2].text.strip()
                    caltech_avg = scores[4].text.strip()
                    data["instructor"][instructor_name][question] = {
                        "score": score,
                        "stdev": stdev,
                        "dept": dept_avg,
                        "caltech": caltech_avg,
                    }

        elif "Comments" in section.text:
            comments = []
            table = section.find_next("table")
            for row in table.find_all("tr"):
                text = row.find("td").text.strip()
                comments.append(text)
            data["comments"] = comments

        elif "Response Rate" in section.text:
            table = section.find_next("table")
            cells = table.find_all("tr")[1].find_all("td")
            numer, denom = float(cells[1].text), float(cells[2].text)
            data["response_rate"] = 0 if denom == 0 else numer / denom

        else:
            if "course" not in data:
                data["course"] = defaultdict(dict)
            tables = []
            sibling = section.find_next_sibling()
            while sibling and sibling.name != "h2":
                if sibling.name == "table":
                    tables.append(sibling)
                sibling = sibling.find_next_sibling()

            for table in tables:
                rows = table.find_all("tr")
                if len(rows) > 1 and (
                    "course average"
                    in rows[1].find("td", class_="questiondiv").text.strip().lower()
                ):
                    question = section.text.split(":")[-1].strip()
                    data["course"][question] = {}
                    for response_cell, option_cell in zip(
                        rows[1].find_all("td", class_="celldiv"),
                        rows[0].find_all("th", class_="celldiv"),
                    ):
                        response, option = (
                            response_cell.text.strip(),
                            option_cell.text.strip(),
                        )
                        data["course"][question][option] = response

                else:
                    for row in rows[1:]:
                        question = row.find("td", class_="questiondiv").text.strip()
                        scores = row.find_all("td", class_="celldiv")
                        score = scores[1].strong.text.strip()
                        stdev = scores[1].contents[2].text[2:].strip()
                        dept_avg = scores[2].text.strip()
                        caltech_avg = scores[4].text.strip()
                        data["course"][question] = {
                            "score": score,
                            "stdev": stdev,
                            "dept": dept_avg,
                            "caltech": caltech_avg,
                        }
    return data


if __name__ == "__main__":
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

    data = defaultdict(dict)

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

    for term in tqdm(RELEVANT_TERMS, desc="Terms"):
        try:
            # wait for table of divisions to load
            driver.find_element(By.LINK_TEXT, term).click()
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tablediv"))
            )

            TERM_URL = driver.current_url

            soup = BeautifulSoup(driver.page_source, "html.parser")
            division_cells = soup.find_all("td", class_="questiondiv")[1:]
            divisions = [cell.get_text(strip=True) for cell in division_cells]
            for division in tqdm(divisions, desc="Divisions", leave=False):
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
                for div in tqdm(dept_divs, desc="Department", leave=False):
                    # collect all links (can't click because stale element)
                    try:
                        dept = div.find_element(By.TAG_NAME, "a").get_attribute("text")
                        if not dept:
                            continue
                        dept_links.append(
                            (
                                dept,
                                div.find_element(By.TAG_NAME, "a").get_attribute(
                                    "href"
                                ),
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
                            course_name = div.find_element(
                                By.TAG_NAME, "a"
                            ).get_attribute("text")
                            if not course_name:
                                continue

                            id = re.sub(
                                r"\b0+(?!\b)",
                                "",
                                course_name.lower().replace("/", "").replace(" ", "-"),
                            )
                            id = re.sub(r"(\d+)(?!$)(?!\d)", r"\1-", id)

                            course_links.append(
                                (
                                    id,
                                    div.find_element(By.TAG_NAME, "a").get_attribute(
                                        "href"
                                    ),
                                )
                            )
                        except NoSuchElementException:
                            pass

                    for id, link in course_links:
                        driver.get(link)
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "survey_title")
                            )
                        )

                        data[id][term] = scrape(driver.page_source, id)

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

    output_path = "./json/tqfr/tqfr.json"
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        print(f"Saved course tqfrs to {output_path}")
    driver.quit()
