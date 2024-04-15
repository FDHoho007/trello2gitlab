#!/bin/python
import json, shutil, os.path, re, tarfile, requests, uuid
from datetime import datetime

GITLAB_REVISION = "63445993282"
GITLAB_VERSION = "15.10.7-ee"
VERSION = "0.2.4"
TRELLO_API_KEY = "5bb9050954a2a56e7a5f22bc41c76b3a"

unixts = "%Y-%m-%dT%H:%M:%SZ"
unixts_ms = "%Y-%m-%dT%H:%M:%S.%fZ"

TrelloColors = {
    "green": "#216e4e",
    "yellow": "#7f5f01",
    "orange": "#974f0c",
    "red": "#ae2a19",
    "purple": "#5e4db2",
    "blue": "#05c",
    "sky": "#206b74",
    "lime": "#4c6b1f",
    "pink": "#943d73",
    "black": "#596773",
    "green_dark": "#164b35",
    "yellow_dark": "#533f04",
    "orange_dark": "#5f3811",
    "red_dark": "#601e16",
    "purple_dark": "#352c63",
    "blue_dark": "#09326c",
    "sky_dark": "#1d474c",
    "lime_dark": "#37471f",
    "pink_dark": "#50253f",
    "black_dark": "#454f59",
    "green_light": "#4bce97",
    "yellow_light": "#e2b203",
    "orange_light": "#faa53d",
    "red_light": "#f87462",
    "purple_light": "#9f8fef",
    "blue_light": "#579dff",
    "sky_light": "#60c6d2",
    "lime_light": "#94c748",
    "pink_light": "#e774bb",
    "black_light": "#8c9bab"
}

def writeToFile(file, content):
    with open(file, "w") as f:
        f.write(content)

def create_label_object(name, color):
    return {
            "title": name,
            "color": "#6699cc" if color is None else color,
            "textColor": "#FFFFFF",
            "type": "ProjectLabel"
        }

def create_member_object(user_id, email, username, access_level):
    return {
            "access_level": access_level,
            "source_type": "Project",
            "user_id": user_id,
            "notification_level":3,
            "created_by_id": None,
            "invite_email": None,
            "invite_accepted_at": None,
            "requested_at": None,
            "expires_at": None,
            "ldap": False,
            "override": False,
            "user": {
                "id": user_id,
                "username": username,
                "public_email": email
            }
        }

def create_note_object(note, author_id, timestamp, system):
    return {
        "note": note,
        "noteable_type": "Issue",
        "author_id": members[author_id]["id"],
        "created_at": timestamp,
        "updated_at": timestamp,
        "attachment": {"url": None},
        "line_code": None,
        "commit_id": None,
        "system": system, 
        "st_diff": None,
        "updated_by_id": None,
        "type": None,
        "position": None,
        "original_position": None,
        "resolved_at": None, 
        "resolved_by_id": None,
        "change_position": None,
        "resolved_by_push": None,
        "confidential": None,
        "last_edited_at": timestamp,
        "author": {},
        "award_emoji": [],
        "system_note_metadata":{
            "commit_count": None,
            "action": "relate",
            "created_at": timestamp,
            "updated_at": timestamp
        },
        "events": []
    }

def create_event_object(action, author_id, timestamp):
    return {
        "author_id": members[author_id]["id"],
        "created_at": timestamp,
        "updated_at": timestamp,
        "action": action
    }

def create_label_event_object(action, label, author_id, timestamp):
    return {
        "action": action,
        "user_id": members[author_id]["id"],
        "created_at": timestamp,
        "label": {"title": label}
    }

def create_state_event_object(state, author_id, timestamp):
    return {
        "user_id": members[author_id]["id"],
        "created_at": timestamp,
        "state": state,
    }

def actions_for_card(actions, card_id):
    list = []
    for e in filter(lambda action: "card" in action["data"] and action["data"]["card"]["id"] == card_id, actions):
        list.append(e)
    return list

def actions_for_card_by_type(actions, card_id):
    list = {}
    for e in filter(lambda action: "card" in action["data"] and action["data"]["card"]["id"] == card_id, actions):
        if not e["type"] in list:
            list[e["type"]] = []
        list[e["type"]].append(e)
    return list

def checklists_for_card(checklists, card_id):
    list = []
    for e in filter(lambda checklist: checklist["idCard"] == card_id, checklists):
        list.append(e)
    return list

# Map Trello card urls to '#<issue id>' as text. GitLab will create a link out of it.
url_id_mapping = {}
mention_mapping = {}
attachment_mapping = {}
def fix_urls(text):
    for url in url_id_mapping.keys():
        text = text.replace(url, "#" + str(url_id_mapping[url]))
    for url in attachment_mapping.keys():
        name = attachment_mapping[url]["name"]
        new_url = "/uploads/" + attachment_mapping[url]["uuid"] + "/" + attachment_mapping[url]["fileName"]
        img = len(attachment_mapping[url]["previews"]) > 0
        url = re.escape(url)
        text = re.sub("!?(\[.+\])?(\(" + url + "\)|" + url + ")", ("!" if img else "") + "[" + name + "](" + new_url + ")", text)
    for username in mention_mapping.keys():
        text = text.replace("@" + username, "@" + mention_mapping[username])
    return text

if not os.path.isfile("board.json"):
    print("Welcome to the Trello2Gitlab Migrator.")
    print("To get started you have to export your trello board.")
    print("If not already opened open your trello issue board now and have a look at the url.")
    print("It should start with 'https://trello.com/b/' followed by some random characters followed by a slash and the name of your board.")
    print("Replace the last slash and your board name with '.json' so that the url is now 'https://trello.com/b/<board id>.json'.")
    print("Download that text dump into a file called 'board.json' in this directory and re-run this script.")
    print("One more reason to finally switch away from Trello is the fact, that their export might not contain all your data.")
    print("This espacially effects large issue boards. You can use this tool to fully export your board: https://github.com/FDHoho007/trello-exporter")
else:
    # Read the Trello export json file
    f = open("board.json", "r")
    trello_export = json.load(f)
    f.close()

    # Prompt for user emails
    print("In order to properly map the trello users to your GitLab users we need some additional information.")
    print("For every upcoming trello username enter the primary email address of the according GitLab user.")
    print("If a trello user has no user account in your GitLab instance, just leave the email emtpy.")
    i = 2 # Member #1 is Ghost User
    members = {}
    # Read user emails from space separated file users.txt
    users = {}
    if os.path.isfile("users.txt"):
        u = open("users.txt", "r")
        for line in u.read().split("\n"):
            user = line.split(" ")
            users[user[0]] = {"name": user[1], "mail": user[2]}
        u.close()
    memberships = {}
    for m in trello_export["memberships"]:
        memberships[m["idMember"]] = m["memberType"]
    members_file = json.dumps(create_member_object(1, "ghost@example.com", "Ghost User", 10))
    for m in trello_export["members"]:
        if m["username"] in users:
            email = users[m["username"]]["mail"]
            username = users[m["username"]]["name"]
        else:
            email = input("Please enter the email address for '" + m["fullName"] + "' (" + m["username"] + "): ")
            username = input("Please enter the gitlab username for '" + m["fullName"] + "' (" + m["username"] + "): ")
        access_level = 50 if memberships[m["id"]] == "admin" else 30
        # If no email is provided, use the ghost user instead
        if email == "":
            members[m["id"]] = {"id": 1, "name": "ghost"}
            mention_mapping[m["username"]] = "ghost"
        else:
            members_file += "\n" + json.dumps(create_member_object(i, email, m["fullName"], access_level))
            members[m["id"]] = {"id": i, "name": username}
            i += 1
            mention_mapping[m["username"]] = username
    # Add all members, that are not listed in members, but as creator of an action
    for a in trello_export["actions"]:
        if "memberCreator" in a:
            m = a["memberCreator"]
            if m["id"] not in members:
                if m["username"] in users:
                    email = users[m["username"]]["mail"]
                    username = users[m["username"]]["name"]
                else:
                    email = input("Please enter the email address for '" + m["fullName"] + "' (" + m["username"] + "): ")
                    username = input("Please enter the gitlab username for '" + m["fullName"] + "' (" + m["username"] + "): ")
                # If no email is provided, use the ghost user instead
                if email == "":
                    members[m["id"]] = {"id": 1, "name": "ghost"}
                    mention_mapping[m["username"]] = "ghost"
                else:
                    members_file += "\n" + json.dumps(create_member_object(i, email, m["fullName"], 10))
                    members[m["id"]] = {"id": i, "name": username}
                    i += 1
                    mention_mapping[m["username"]] = username
        else:
            members[a["idMemberCreator"]] = {"id": 1, "name": "ghost"}
    print("All user information gathered.")

    # Prepare GitLab export by creating basic folder structure
    if os.path.isdir("gitlab-export"):
        shutil.rmtree("gitlab-export")
    os.mkdir("gitlab-export")
    writeToFile("gitlab-export/GITLAB_REVISION", GITLAB_REVISION)
    writeToFile("gitlab-export/GITLAB_VERSION", GITLAB_VERSION)
    writeToFile("gitlab-export/VERSION", VERSION)
    os.mkdir("gitlab-export/tree")
    writeToFile("gitlab-export/tree/project.json", json.dumps({"description": trello_export["desc"]}))
    os.mkdir("gitlab-export/tree/project")
    writeToFile("gitlab-export/tree/project/project_members.ndjson", members_file)

    # Import labels and lists (as scoped labels)
    labels = {}
    lables_file = ""
    for label in trello_export["labels"]:
        labels[label["id"]] = label["name"]
        lables_file += "\n" + json.dumps(create_label_object(label["name"], TrelloColors[label["color"]]))
    board_lists = []
    i = 0
    for list in sorted(trello_export["lists"], key=lambda x: x["pos"]):
        labels[list["id"]] = "list::" + list["name"]
        label = create_label_object("list::" + list["name"], None)
        lables_file += "\n" + json.dumps(label)
        # Lists will be imported as scoped labels and added to a new board
        if not list["closed"]:
            board_lists.append({
                "list_type": "label",
                "position": i,
                "label": label
            })
        i += 1
    if lables_file != "":
        writeToFile("gitlab-export/tree/project/labels.ndjson", lables_file[1:])
    writeToFile("gitlab-export/tree/project/boards.ndjson", json.dumps({"name": "Trello", "lists": board_lists}))

    for card in trello_export["cards"]:
        url_id_mapping[card["url"]] = card["idShort"]
        for attachment in card["attachments"]:
            if attachment["isUpload"]:
                attachment_mapping[attachment["url"]] = attachment
                attachment_mapping[attachment["url"]]["uuid"] = str(uuid.uuid4()).replace("-", "").lower()
                attachment_mapping[attachment["url"]]["fileName"] = re.sub(r"[^a-zA-Z0-9._-]", "_", attachment_mapping[attachment["url"]]["fileName"])


    # Import issues
    issues_file = ""
    i = 0
    comments_count_should = 0
    comments_count_is = 0
    for card in trello_export["cards"]:
        card["actions"] = actions_for_card(trello_export["actions"], card["id"])
        card["actionsByType"] = actions_for_card_by_type(trello_export["actions"], card["id"])
        card["checklists"] = checklists_for_card(trello_export["checklists"], card["id"])
        actionCreate = None
        actionClosed = None
        actionFirstJoinedMember = None
        actionLatest = None
        events = []
        label_events = []
        state_events = []
        notes = []
        for action in card["actions"]:
            type = action["type"]
            #memberCreator = action["memberCreator"] if "memberCreator" in action else {"id": action["idMemberCreator"], "fullName": "Ghost User"}
            memberName = "ghost"
            if "idMember" in action["data"] and action["data"]["idMember"] in members:
                memberName = members[action["data"]["idMember"]]["name"]
            if type == "createCard":
                actionCreate = action
                events.append(create_event_object("created", action["idMemberCreator"], action["date"]))
            elif type == "deleteCard":
                # TODO
                pass
            elif type == "updateCard":
                if actionLatest is None or datetime.strptime(actionLatest["date"], unixts_ms) < datetime.strptime(action["date"], unixts_ms):
                    actionLatest = action
                if "closed" in action["data"]["old"]:
                    if action["data"]["card"]["closed"]:
                        events.append(create_event_object("closed", action["idMemberCreator"], action["date"]))
                        state_events.append(create_state_event_object("closed", action["idMemberCreator"], action["date"]))
                        if actionClosed is None or datetime.strptime(actionClosed["date"], unixts_ms) < datetime.strptime(action["date"], unixts_ms):
                            actionClosed = action
                    else:
                        events.append(create_event_object("reopened", action["idMemberCreator"], action["date"]))
                        state_events.append(create_state_event_object("reopened", action["idMemberCreator"], action["date"]))
                if "idList" in action["data"]["old"]:
                    label_events.append(create_label_event_object("remove", "list::" + action["data"]["listBefore"]["name"], action["idMemberCreator"], action["date"]))
                    label_events.append(create_label_event_object("add", "list::" + action["data"]["listAfter"]["name"], action["idMemberCreator"], action["date"]))
            elif type == "commentCard":
                note = create_note_object(fix_urls(action["data"]["text"]), action["idMemberCreator"], action["date"], False)
                for reaction in action["reactions"]:
                    note["award_emoji"].append({"name": reaction["emoji"]["shortName"], "user_id": members[reaction["idMember"]]["id"]})
                notes.append(note)
                comments_count_is += 1
            elif type == "addMemberToCard":
                if actionFirstJoinedMember is None:
                    actionFirstJoinedMember = action
                notes.append(create_note_object("assigned to @" + memberName, action["idMemberCreator"], action["date"], True))
            elif type == "removeMemberFromCard":
                notes.append(create_note_object("unassigned @" + memberName, action["idMemberCreator"], action["date"], True))
            elif type == "addChecklistToCard" or type == "removeChecklistFromCard" or type == "updateCheckItemStateOnCard":
                # Checklist changes aren't logged in GitLab
                pass
            elif type == "addAttachmentToCard" or type == "deleteAttachmentFromCard" or type == "updateCheckItemStateOnCard":
                # Attachments changes aren't logged in GitLab
                pass
            else:
                print("Unknown action type " + type)
        comments_count_should += card["badges"]["comments"]
        for attachment in card["attachments"]:
            if attachment["isUpload"]:
                notes.append(create_note_object(fix_urls(attachment["url"]), attachment["idMember"], attachment["date"], False))
            else:
                notes.append(create_note_object(fix_urls("[" + attachment["name"] + "](" + attachment["url"] + ")"), attachment["idMember"], attachment["date"], False))
        # If we have no createCard action we assume the first joined member to be the creator
        if actionCreate is None:
            actionCreate = actionFirstJoinedMember
        if actionCreate is not None and "list" in actionCreate["data"] and "name" in actionCreate["data"]["list"]:
            label_events.append(create_label_event_object("add", "list::" + actionCreate["data"]["list"]["name"], actionCreate["idMemberCreator"], actionCreate["date"]))
        description = fix_urls(card["desc"])
        for checklist in card["checklists"]:
            if description != "":
                description += "\n\n"
            description += checklist["name"]
            if not description.endswith(":"):
                description += ":"
            description += "\n"
            for item in checklist["checkItems"]:
                description += "- [" + ("X" if item["state"] == "complete" else " ") + "] " + item["name"] + "\n"
        issue = {
            "title": card["name"],
            "author_id": members[actionCreate["idMemberCreator"]]["id"] if actionCreate is not None else 1,
            "created_at": actionCreate["date"] if actionCreate is not None else card["dateLastActivity"],
            "updated_at": actionLatest["date"] if actionLatest is not None else card["dateLastActivity"],
            "updated_by_id": members[actionLatest["idMemberCreator"]]["id"] if actionLatest is not None else None,
            "last_edited_at": actionLatest["date"] if actionLatest is not None else card["dateLastActivity"],
            "last_edited_by_id": members[actionLatest["idMemberCreator"]]["id"] if actionLatest is not None else None,
            "description": description,
            "iid": card["idShort"],
            "confidential": False,
            "due_date": card["due"],
            "lock_version": 0,
            "time_estimate": 0,
            "relative_position": card["pos"],
            "discussion_locked": None,
            "state": "closed" if card["closed"] else "opened",
            "closed_at": actionClosed["date"] if actionClosed is not None else None,
            "closed_by_id": members[actionClosed["idMemberCreator"]]["id"] if actionClosed is not None else None,
            "weight": None,
            "health_status": None,
            "external_key": None,
            "issue_type": "issue",
            "events": events,
            "timelogs": [],
            "notes": notes,
            "label_links": [{"label": {"title": labels[card["idList"]]}}] + [{"label": {"title": labels[label_id]}} for label_id in card["idLabels"]],
            "resource_label_events": label_events,
            "resource_milestone_events": [],
            "resource_state_events": state_events,
            "designs": [],
            "design_version": [],
            "issue_assignees": [{"user_id": members[m]["id"]} for m in card["idMembers"]],
            "zoom_meetings": [],
            "award_emoji": [],
            "resource_iteration_events": []
        }
        issues_file += "\n" + json.dumps(issue)
        i += 1
    if issues_file != "":
        writeToFile("gitlab-export/tree/project/issues.ndjson", issues_file[1:])

    # Download attachments
    if len(attachment_mapping.keys()) > 0:
        trello_token = input("Please enter your Trello API token, which was shown on the Trello Exporter page: ")
        os.mkdir("gitlab-export/uploads")
        for attachment_id in attachment_mapping.keys():
            attachment = attachment_mapping[attachment_id]
            os.mkdir("gitlab-export/uploads/" + attachment["uuid"])
            r = requests.get(attachment["url"], headers={"Authorization": "OAuth oauth_consumer_key=\"" + TRELLO_API_KEY + "\", oauth_token=\"" + trello_token + "\""})
            if r.status_code == 200:
                with open("gitlab-export/uploads/" + attachment["uuid"] + "/" + attachment["fileName"], "wb") as out:
                    for bits in r.iter_content():
                        out.write(bits)

    # Finish up by zipping the export folder
    with tarfile.open("gitlab-export.tar.gz", "w:gz") as tar:
        tar.add("gitlab-export", arcname=os.path.sep)
    shutil.rmtree("gitlab-export")
    print("Trello2Gitlab Migration succeeded.")
    print("You can now import the file 'gitlab-export.tar.gz' as a new project into your GitLab instance.")