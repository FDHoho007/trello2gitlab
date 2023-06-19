#!/bin/python
import json, shutil, os.path, tarfile
from trello_colors import TrelloColors

def writeToFile(file, content):
    with open(file, "w") as f:
        f.write(content)

def create_label(name, color):
    return {
            "title": name,
            "color": "#6699cc" if color is None else color,
            "textColor": "#FFFFFF",
            "type": "ProjectLabel"
        }

def actions_for_card(actions, card_id):
    list = []
    for e in filter(lambda action: "card" in action["data"] and action["data"]["card"]["id"] == card_id, actions):
        list.append(e)
    return list

def checklists_for_card(checklists, card_id):
    list = []
    for e in filter(lambda checklist: checklist["idCard"] == card_id, checklists):
        list.append(e)
    return list

def fix_urls(text):
    return text

if not os.path.isfile("board.json"):
    print("Welcome to the Trello2Gitlab Migrator.")
    print("To get started you have to export your trello board.")
    print("If not already opened open your trello issue board now and have a look at the url.")
    print("It should start with 'https://trello.com/b/' followed by some random characters followed by a slash and the name of your board.")
    print("Replace the last slash and your board name with '.json' so that the url is now 'https://trello.com/b/<board id>.json'.")
    print("Download that text dump into a file called 'board.json' in this directory and re-run this script.")
else:
    f = open("board.json", "r")
    trello_export = json.load(f)
    f.close()

    if os.path.isdir("gitlab-export"):
        shutil.rmtree("gitlab-export")
    os.mkdir("gitlab-export")
    writeToFile("gitlab-export/GITLAB_REVISION", "63445993282")
    writeToFile("gitlab-export/GITLAB_VERSION", "15.10.7-ee")
    writeToFile("gitlab-export/VERSION", "0.2.4")
    os.mkdir("gitlab-export/tree")
    writeToFile("gitlab-export/tree/project.json", json.dumps({"description": trello_export["desc"]}))
    os.mkdir("gitlab-export/tree/project")

    # Import labels and lists (as scoped labels)
    lables_file = ""
    for label in trello_export["labels"]:
        lables_file += "\n" + json.dumps(create_label(label["name"], TrelloColors[label["color"]]))
    board_lists = []
    i = 0
    for list in sorted(trello_export["lists"], key=lambda x: x["pos"]):
        label = create_label("list::" + list["name"], None)
        lables_file += "\n" + json.dumps(label)
        board_lists.append({
            "list_type": "label",
            "position": i,
            "label": label
        })
        i += 1
    if lables_file != "":
        writeToFile("gitlab-export/tree/project/labels.ndjson", lables_file[1:])
    writeToFile("gitlab-export/tree/project/boards.ndjson", json.dumps({"name": "Trello", "lists": board_lists}))

    # Import issues
    issues_file = ""
    i = 0
    for card in trello_export["cards"]:
        card["actions"] = actions_for_card(trello_export["actions"], card["id"])
        card["checklists"] = checklists_for_card(trello_export["checklists"], card["id"])
        issue = {
            "title": card["name"],
            "author_id": 0, # TODO
            "created_at": "", # TODO
            "updated_at": "", # TODO
            "description": fix_urls(card["desc"]),
            "iid": 0, # TODO
            "updated_by_id": 0, # TODO,
            "confidential": False
        }
        # TODO: Card to JSON
        i += 1
    if issues_file != "":
        writeToFile("gitlab-export/tree/project/issues.ndjson", issues_file[1:])

    with tarfile.open("gitlab-export.tar.gz", "w:gz") as tar:
        tar.add("gitlab-export", arcname=os.path.sep)
    shutil.rmtree("gitlab-export")
    print("Trello2Gitlab Migration succeeded.")
    print("You can now import the file 'gitlab-export.tar.gz' as a new project into your GitLab instance.")

#{"title":"Testissue","author_id":800,"created_at":"2023-06-19T19:51:37.509+02:00","updated_at":"2023-06-19T19:51:37.509+02:00","description":"A sample issue","iid":1,"updated_by_id":null,"confidential":false,"due_date":null,"lock_version":0,"time_estimate":0,"relative_position":513,"last_edited_at":null,"last_edited_by_id":null,"discussion_locked":null,"closed_at":null,"closed_by_id":null,"weight":null,"health_status":null,"external_key":null,"issue_type":"issue","state":"opened","events":[{"project_id":2286,"author_id":800,"created_at":"2023-06-19T19:51:38.241+02:00","updated_at":"2023-06-19T19:51:38.241+02:00","action":"created","target_type":"Issue","fingerprint":null}],"timelogs":[],"notes":[{"note":"A comment","noteable_type":"Issue","author_id":800,"created_at":"2023-06-19T19:51:46.570+02:00","updated_at":"2023-06-19T19:51:46.570+02:00","project_id":2286,"attachment":{"url":null},"line_code":null,"commit_id":null,"system":false,"st_diff":null,"updated_by_id":null,"type":null,"position":null,"original_position":null,"resolved_at":null,"resolved_by_id":null,"discussion_id":"528b0b6bc6f0d378a70b3abecddd191060fe81ae","change_position":null,"resolved_by_push":null,"confidential":null,"last_edited_at":"2023-06-19T19:51:46.570+02:00","author":{"name":"Fabian Dietrich"},"award_emoji":[],"events":[{"project_id":2286,"author_id":800,"created_at":"2023-06-19T19:51:46.753+02:00","updated_at":"2023-06-19T19:51:46.753+02:00","action":"commented","target_type":"Note","fingerprint":null}]},{"note":"assigned to @dietrich","noteable_type":"Issue","author_id":800,"created_at":"2023-06-19T19:51:37.886+02:00","updated_at":"2023-06-19T19:51:37.889+02:00","project_id":2286,"attachment":{"url":null},"line_code":null,"commit_id":null,"system":true,"st_diff":null,"updated_by_id":null,"type":null,"position":null,"original_position":null,"resolved_at":null,"resolved_by_id":null,"discussion_id":"29e79042cb9dda013f2344617c13b9fceb84a27f","change_position":null,"resolved_by_push":null,"confidential":null,"last_edited_at":"2023-06-19T19:51:37.889+02:00","author":{"name":"Fabian Dietrich"},"award_emoji":[],"system_note_metadata":{"commit_count":null,"action":"assignee","created_at":"2023-06-19T19:51:37.920+02:00","updated_at":"2023-06-19T19:51:37.920+02:00"},"events":[]},{"note":"marked this issue as related to #2","noteable_type":"Issue","author_id":800,"created_at":"2023-06-19T19:52:29.697+02:00","updated_at":"2023-06-19T19:52:29.699+02:00","project_id":2286,"attachment":{"url":null},"line_code":null,"commit_id":null,"system":true,"st_diff":null,"updated_by_id":null,"type":null,"position":null,"original_position":null,"resolved_at":null,"resolved_by_id":null,"discussion_id":"2e908f922a12aeca5e5d1f743da52380770fe5d2","change_position":null,"resolved_by_push":null,"confidential":null,"last_edited_at":"2023-06-19T19:52:29.699+02:00","author":{"name":"Fabian Dietrich"},"award_emoji":[],"system_note_metadata":{"commit_count":null,"action":"relate","created_at":"2023-06-19T19:52:29.727+02:00","updated_at":"2023-06-19T19:52:29.727+02:00"},"events":[]}],"label_links":[{"target_type":"Issue","created_at":"2023-06-19T19:51:37.743+02:00","updated_at":"2023-06-19T19:51:37.743+02:00","label":{"title":"bug","color":"#d9534f","project_id":2286,"created_at":"2023-06-19T19:50:00.285+02:00","updated_at":"2023-06-19T19:50:00.285+02:00","template":false,"description":null,"group_id":null,"type":"ProjectLabel","priorities":[]}},{"target_type":"Issue","created_at":"2023-06-19T19:51:37.746+02:00","updated_at":"2023-06-19T19:51:37.746+02:00","label":{"title":"enhancement","color":"#5cb85c","project_id":2286,"created_at":"2023-06-19T19:50:00.436+02:00","updated_at":"2023-06-19T19:50:00.436+02:00","template":false,"description":null,"group_id":null,"type":"ProjectLabel","priorities":[]}},{"target_type":"Issue","created_at":"2023-06-19T19:51:37.747+02:00","updated_at":"2023-06-19T19:51:37.747+02:00","label":{"title":"list::todo","color":"#6699cc","project_id":2286,"created_at":"2023-06-19T19:50:15.507+02:00","updated_at":"2023-06-19T19:50:15.507+02:00","template":false,"description":"","group_id":null,"type":"ProjectLabel","priorities":[]}}],"resource_label_events":[{"action":"add","user_id":800,"created_at":"2023-06-19T19:51:37.842+02:00","label":{"title":"bug","color":"#d9534f","project_id":2286,"created_at":"2023-06-19T19:50:00.285+02:00","updated_at":"2023-06-19T19:50:00.285+02:00","template":false,"description":null,"group_id":null,"type":"ProjectLabel","priorities":[]}},{"action":"add","user_id":800,"created_at":"2023-06-19T19:51:37.842+02:00","label":{"title":"enhancement","color":"#5cb85c","project_id":2286,"created_at":"2023-06-19T19:50:00.436+02:00","updated_at":"2023-06-19T19:50:00.436+02:00","template":false,"description":null,"group_id":null,"type":"ProjectLabel","priorities":[]}},{"action":"add","user_id":800,"created_at":"2023-06-19T19:51:37.842+02:00","label":{"title":"list::todo","color":"#6699cc","project_id":2286,"created_at":"2023-06-19T19:50:15.507+02:00","updated_at":"2023-06-19T19:50:15.507+02:00","template":false,"description":"","group_id":null,"type":"ProjectLabel","priorities":[]}}],"resource_milestone_events":[],"resource_state_events":[],"designs":[],"design_versions":[],"issue_assignees":[{"user_id":800}],"zoom_meetings":[],"award_emoji":[],"resource_iteration_events":[]}
#{"title":"Closed issue","author_id":800,"created_at":"2023-06-19T19:52:29.410+02:00","updated_at":"2023-06-19T19:52:40.065+02:00","description":"This will be closed","iid":2,"updated_by_id":null,"confidential":false,"due_date":null,"lock_version":0,"time_estimate":0,"relative_position":1026,"last_edited_at":null,"last_edited_by_id":null,"discussion_locked":null,"closed_at":"2023-06-19T19:52:40.001+02:00","closed_by_id":800,"weight":null,"health_status":null,"external_key":null,"issue_type":"issue","state":"closed","events":[{"project_id":2286,"author_id":800,"created_at":"2023-06-19T19:52:29.563+02:00","updated_at":"2023-06-19T19:52:29.563+02:00","action":"created","target_type":"Issue","fingerprint":null},{"project_id":2286,"author_id":800,"created_at":"2023-06-19T19:52:40.136+02:00","updated_at":"2023-06-19T19:52:40.136+02:00","action":"closed","target_type":"Issue","fingerprint":null}],"timelogs":[],"notes":[{"note":"marked this issue as related to #1","noteable_type":"Issue","author_id":800,"created_at":"2023-06-19T19:52:29.645+02:00","updated_at":"2023-06-19T19:52:29.647+02:00","project_id":2286,"attachment":{"url":null},"line_code":null,"commit_id":null,"system":true,"st_diff":null,"updated_by_id":null,"type":null,"position":null,"original_position":null,"resolved_at":null,"resolved_by_id":null,"discussion_id":"bec69ca87036cd5fc3f19b1485ef56089fead9d3","change_position":null,"resolved_by_push":null,"confidential":null,"last_edited_at":"2023-06-19T19:52:29.647+02:00","author":{"name":"Fabian Dietrich"},"award_emoji":[],"system_note_metadata":{"commit_count":null,"action":"relate","created_at":"2023-06-19T19:52:29.675+02:00","updated_at":"2023-06-19T19:52:29.675+02:00"},"events":[]},{"note":"assigned to @dietrich","noteable_type":"Issue","author_id":800,"created_at":"2023-06-19T19:52:29.750+02:00","updated_at":"2023-06-19T19:52:29.752+02:00","project_id":2286,"attachment":{"url":null},"line_code":null,"commit_id":null,"system":true,"st_diff":null,"updated_by_id":null,"type":null,"position":null,"original_position":null,"resolved_at":null,"resolved_by_id":null,"discussion_id":"0fe292ae0adae728b64972dd80c1d0fbafa7e951","change_position":null,"resolved_by_push":null,"confidential":null,"last_edited_at":"2023-06-19T19:52:29.752+02:00","author":{"name":"Fabian Dietrich"},"award_emoji":[],"system_note_metadata":{"commit_count":null,"action":"assignee","created_at":"2023-06-19T19:52:29.778+02:00","updated_at":"2023-06-19T19:52:29.778+02:00"},"events":[]}],"label_links":[],"resource_label_events":[],"resource_milestone_events":[],"resource_state_events":[{"user_id":800,"created_at":"2023-06-19T19:52:40.150+02:00","state":"closed","source_commit":null,"close_after_error_tracking_resolve":false,"close_auto_resolve_prometheus_alert":false}],"designs":[],"design_versions":[],"issue_assignees":[{"user_id":800}],"zoom_meetings":[],"award_emoji":[],"resource_iteration_events":[]}
