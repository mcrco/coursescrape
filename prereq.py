import json
import re


def has_no_numbers(string):
    for char in string:
        if char.isnumeric():
            return False
    return True


def extract_prereqs(prereq_text):
    depts = ["cms", "ma", "ee", "ph", "ay", "mce"]

    courses = {}
    for dept in depts:
        with open(f"json/{dept}.json") as f:
            dept_courses = json.load(f)
            courses.update(dept_courses)

    prefixes = ["ma", "ee", "ph", "acm", "ids", "ay", "cs", "me"]
    escaped_strings = [re.escape(s) for s in prefixes]
    pattern = (
        rf"(?:{'|'.join(escaped_strings)})(?:/(?:{'|'.join(escaped_strings)}))* \d+"
    )
    regex = re.compile(pattern)

    if not prereq_text:
        return []

    text = prereq_text.lower()
    prereqs = set()
    matches = regex.findall(text)

    for match in matches:
        for id, course in courses.items():
            course_id = course["course_id"].lower()
            if match == course_id:
                prereqs.add(id)
            elif match in course_id:
                idx = course_id.index(match) + len(match)
                if (
                    idx == len(course_id)
                    or course_id[idx] == "/"
                    or has_no_numbers(course_id[idx:])
                ):
                    prereqs.add(id)

    return list(prereqs) if prereqs else []
