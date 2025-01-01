from bs4 import BeautifulSoup
import os
import json
import re
from collections import defaultdict

TQFR_DIR = "html/tqfr"
RELEVANT_TERMS = [
    "FA 2023-24",
    "WI 2023-24",
    "SP 2023-24",
    "FA 2022-23",
    "WI 2022-23",
    "SP 2022-23",
]


def scrape_html(fpath):
    with open(fpath, "r") as f:
        soup = BeautifulSoup(f, "html.parser")

    course_id = os.path.basename(fpath).split(".")[0]
    headers = soup.find_all("h1")
    if not headers:
        print(fpath)
        return
    title, course_name = headers[0], headers[1].text.strip()
    course_id = re.sub(r"\b0+(\d+)", r"\1", title.text.strip().split(" — ")[1])
    data = {"id": course_id, "course_id": course_id, "name": course_name}

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
            data["response_rate"] = float(cells[1].text) / float(cells[2].text)

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


with open("test_ph1a.json", "w", encoding="utf-8") as f:
    json.dump(
        scrape_html("./html/tqfr/FA 2022-23/PMA/Physics/ph-1-a.html"), f, indent=4
    )

with open("test_cs1.json", "w", encoding="utf-8") as f:
    json.dump(
        scrape_html("./html/tqfr/FA 2022-23/EAS/Computer Science/cs-1.html"),
        f,
        indent=4,
    )

course_data = defaultdict(dict)
for term in RELEVANT_TERMS:
    term_path = os.path.join(TQFR_DIR, term)
    if not os.path.isdir(term_path):
        continue
    for division in os.listdir(term_path):
        division_path = os.path.join(term_path, division)
        if not os.path.isdir(division_path):
            continue
        for dept in os.listdir(division_path):
            dept_path = os.path.join(division_path, dept)
            if not os.path.isdir(dept_path):
                continue
            for fname in os.listdir(dept_path):
                fpath = os.path.join(dept_path, fname)
                course_id = os.path.basename(fpath).split(".")[0]
                course_data[course_id][term] = scrape_html(fpath)

output_path = "./json/tqfr/tqfr.json"
if not os.path.exists(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(course_data, f, indent=4)
    print(f"Saved course tqfrs to {output_path}")
