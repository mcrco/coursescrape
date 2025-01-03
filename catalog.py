from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from json_util import save_courses
from prereq import extract_prereqs


def scrape(dept):
    url = f"https://www.catalog.caltech.edu/current/2024-25/department/{dept}"
    response = requests.get(url)
    if not response.status_code == 200:
        print(
            f"Failed to retrieve the {dept.upper()} courses. Status code: {response.status_code}"
        )
        return

    soup = BeautifulSoup(response.text, "html.parser")

    entries = soup.find_all("div", class_="course-description2")
    courses = {}
    for div in entries:
        id = div.get("id")
        course_id = div.find("div", class_="course-description2__label").get_text(
            strip=True
        )
        name = div.find("h2", class_="course-description2__title").get_text(strip=True)
        link = url + "/" + "-".join([token.lower() for token in name.split()])

        units = ""
        terms = ""
        units_terms = div.find(
            "div", class_="course-description2__units-and-terms"
        ).find_all("span")
        for item in units_terms:
            item_text = item.get_text(strip=True)
            if "unit" in item_text:
                units = item_text
            else:
                terms = item_text

        try:
            description = (
                div.find("div", class_="course-description2__description")
                .find("p")
                .get_text(strip=True)
            )
        except AttributeError:
            print(course_id, "does not have any description.")
            description = ""

        offered = "Not offered" not in description

        try:
            instructor_div = div.find("div", class_="course-description2__instructors")
            instructors = instructor_div.get_text(strip=True).split(":")[1]
        except AttributeError:
            # print(div)
            print(course_id, "does not have any instructors.")
            instructors = ""

        try:
            prereq_text = div.find(
                "div", class_="course-description2__prerequisites"
            ).get_text(strip=True)
        except AttributeError:
            print(course_id, "does not have any prereqs.")
            prereq_text = ""

        courses[id] = {
            "id": id,
            "course_id": course_id,
            "name": name,
            "units": units,
            "terms": terms,
            "description": description,
            "offered": offered,
            "instructors": instructors,
            "link": link,
            "prereq_text": prereq_text,
        }

    return courses


if __name__ == "__main__":
    driver = webdriver.Chrome()
    url = "https://www.catalog.caltech.edu/current/2024-25/"
    driver.get(url)

    # wait til page loads
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "sidebar-menu-block__level-3__item__wrapper")
        )
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    courses_section = soup.find_all("li", class_="sidebar-menu-block__level-2__item")[4]
    links = courses_section.find_all("a", class_="sidebar-menu-block__level-3__link")
    course_dict = {}
    for link in links:
        dept = link.get("href").split("/")[-2].lower()
        print(dept)
        course_dict[dept] = scrape(dept)

    courses = {}
    for dept_courses in course_dict.values():
        courses.update(dept_courses)

    for dept, dept_courses in course_dict.items():
        for id, course in dept_courses.items():
            dept_courses[id]["prereqs"] = extract_prereqs(
                course["prereq_text"], courses
            )
            if "prereqs" not in courses[id]:
                courses[id]["prereqs"] = []
            for prereq in dept_courses[id]["prereqs"]:
                if prereq not in courses[id]["prereqs"]:
                    courses[id]["prereqs"].append(prereq)
        save_courses(dept_courses, dept)

    save_courses(courses, "catalog")
