# Trello2GitLab

This python script helps you to migrate your Trello issue board into a GitLab project issue board.
It uses an export of your Trello board to then generate a valid GitLab export file,
which in turn can be used to import as a GitLab project containing your issues.

This project is inspired by https://gitlab.com/tristanpct/trello2gitlab/ which
* did not work anymore when I tried to use it in 2023
* has to be compiled
* needs API Access and therefore some tokens aquired by hand

**Note**: The offical trello export might drop some items if they surpass a certain limit due to performance in their backend. You can still get a complete export using [this](https://github.com/FDHoho007/trello-exporter) tool.

**Note**: This is a best effot script. Some required information like dates, that are not given through the export, might be guessed from other information.

## Usage

The python script is guided. Therefore just download the trello2gitlab.py and run it.

Tip: Instead of providing the user-email mappings over stdin you can create a users.txt containing trello usernames/gitlab email email mappings separated by newlines.

## Supportd Features
* Title
* Description
* Dates
* Asignees
* Lists
* Labels
* Comments
* Checklists
* Reactions
* Attachments

## Not supported yet
* Custom Fields
* PowerUps