from bs4 import BeautifulSoup
import requests
import os

from json_util import save_courses
from prereq import extract_prereqs


def gen_cmsee(dept):
    html_file = f"html/{dept.lower()}.html"
    url = f"https://www.{dept}.caltech.edu/academics/courses"
    if not os.path.exists(html_file):
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

    entries = soup.find_all("div", class_="course-description2")
    courses = {}
    for div in entries:
        id = div.get("id")
        course_id = div.find("span", class_="course-description2__label").get_text(
            strip=True
        )
        name = div.find("span", class_="course-description2__title").get_text(
            strip=True
        )
        link = url + div.find("a", class_="course-description2__link").get("href")

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
            for span in instructor_div.find_all("span"):
                span.decompose()
            instructors = instructor_div.get_text(strip=True)
        except AttributeError:
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

    for id, course in courses.items():
        courses[id]["prereqs"] = extract_prereqs(course["prereq_text"])
    save_courses(courses, dept.lower())


if __name__ == "__main__":
    gen_cmsee("CMS")
    gen_cmsee("EE")
    gen_cmsee("MCE")
