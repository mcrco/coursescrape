import json
import os


# Save courses to dept.json
def save_courses(courses: dict, dept: str):
    file = f"{dept}.json"
    with open(os.path.join("json", file), "w", encoding="utf-8") as json_file:
        json.dump(courses, json_file, indent=4)
    print(f"{dept.upper()} courses (prereqs as text) saved to {file}")


# Save courses with just id, name and prereq text (smaller file for llm)
def save_courses_prereq_text(courses: dict, dept: str):
    prereq_text_file = f"{dept}_prereqtext.json"
    filtered_dict = {
        id: {k: v for k, v in course.items() if k in ["id", "name", "prereq_text"]}
        for id, course in courses.items()
    }
    with open(
        os.path.join("json/llm", prereq_text_file), "w", encoding="utf-8"
    ) as json_file:
        json.dump(filtered_dict, json_file, indent=4)
    print(
        f"{dept.upper()} courses with only prereq text information saved to {prereq_text_file}"
    )


# Merge (llm?) generated prereq arrays from external file if possible
def merge_llm(dept: str):
    basic_file = f"{dept}.json"
    with open(os.path.join("json", basic_file), "r", encoding="utf-8") as json_file:
        courses = json.load(json_file)

    prereq_file = f"{dept}_prereqs.json"
    if os.path.exists(os.path.join("json/llm", prereq_file)):
        with open(os.path.join("json", prereq_file), "r") as json_file:
            prereqs = json.load(json_file)
        for key in courses:
            if key in prereqs:
                courses[key]["prereqs"] = prereqs[key]["prereqs"]
                for prereq in courses[key]["prereqs"]:
                    if prereq == courses[key]["id"]:
                        courses[key]["prereqs"].remove(prereq)
        out_file = f"{dept}.json"
        with open(os.path.join("json", out_file), "w", encoding="utf-8") as json_file:
            json.dump(courses, json_file, indent=4)
        print(f"{dept.upper()} courses (with prereq arrays) saved to '{out_file}'")
    else:
        print(f"Unable to merge prereq array: {prereq_file} not found.")
