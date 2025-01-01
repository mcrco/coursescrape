from bs4 import BeautifulSoup
import requests
import os

from json_util import save_courses
from prereq import extract_prereqs


def scrape_pma(dept):
    html_file = f"html/{dept.lower()}.html"
    url = f"https://pma.caltech.edu/courses/department/{dept.lower()}"
    if os.path.exists(html_file):
        backup_file = f"{html_file}.bak"
        os.rename(html_file, backup_file)
        print(f"{html_file} already exists. Backed up at {backup_file}.")

    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"{dept} course website downloaded and saved as {html_file}.")
    else:
        print(
            f"Failed to retrieve the {dept} courses. Status code: {response.status_code}"
        )

    with open(html_file, "r") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    entries = soup.find_all("div", class_="course-description")
    courses = {}
    for div in entries:
        id = div.get("id")
        course_id = div.find("span", class_="course-description__label").get_text(
            strip=True
        )[:-1]
        name = div.find("span", class_="course-description__title").get_text(
            strip=True
        )[:-1]
        link = url

        units = ""
        try:
            units = div.find("span", class_="course-description__units").get_text(
                strip=True
            )[:-1]
        except AttributeError:
            print(f"{course_id} does not provide number of units.")

        terms = ""
        try:
            terms = div.find("span", class_="course-description__terms").get_text(
                strip=True
            )[:-1]
        except AttributeError:
            print(f"{course_id} does not provide its offered terms.")

        try:
            description = div.find(
                "span", class_="course-description__description"
            ).get_text(strip=True)
        except AttributeError:
            print(course_id, "does not have any description.")
            description = ""

        offered = "Not offered" not in description

        try:
            instructor_div = div.find("span", class_="course-description__instructors")
            instructor_text = instructor_div.get_text(strip=True).split()
            instructors = "No instructors provided."
            for i, token in enumerate(instructor_text):
                if "Instructor" in token:
                    instructors = " ".join(instructor_text[i + 1 :])
                    break
        except AttributeError:
            print(course_id, "does not have any instructors listed.")
            instructors = ""

        try:
            prereq_text = div.find(
                "span", class_="course-description__prerequisites"
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

    for id, course in courses.items():
        courses[id]["prereqs"] = extract_prereqs(course["prereq_text"])
    save_courses(courses, dept.lower())
    print(f"Finished scraping {dept} courses.\n")


if __name__ == "__main__":
    scrape_pma("Ma")
    scrape_pma("Ph")
    scrape_pma("Ay")
