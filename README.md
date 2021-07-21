# UBC-Course-Scout
A Python 3.8 program with a graphical user interface to aid with UBC course registration.
## About
UBC Course Scout is a course registration tool that can automatically register for desired courses when a seat is available.
It uses web-scraping to find the number of seats for a given course section, and will notify the user or register in the course
once a spot is available depending on the user's preferences.

The program takes advantage of an automated browser to facilitate automatic registration.
## Adding a course to watch-list
To add a course to the watch-list, the following info is required and can be entered into their respective boxes:
- Session _(e.g. Winter)_
- Year _(e.g. 2021)_
- Department _(e.g. CPSC)_
- Course # _(e.g. 320)_
- Section _(e.g. 101)_

Once the course section is added, the user can specify whether to only consider the number of general seats remaining, and
if the program should automatically register in the section once it is available.
## Switching courses
To facilitate automatically dropping one course for another, the user can optionally add a "rule".
  
To get started, the preferred course must first be added to the watch-list. Then, the user can specify which course(s) they
want to drop once the watch-listed course is available, and it will be added to the rule-list.

Once a watch-listed course is available, and the user has entered their CWL login, then the program will
proceed to drop the course(s) specified in the rule immediately before registering.
## Notes
- In order for the auto-registration feature to take effect, the user must enter and confirm their CWL login in the settings
  tab.
- Courses and rules added to the program will be saved to disk and persist between sessions.
    - For security reasons, the user's CWL login  will NOT be saved to disk and will need to be entered again between
  sessions.
- If the refresh timer is active and there are no more valid sections to monitor (e.g. all the sections are invalid or have been successfully registered in), the refresh timer will stop automatically.
    - It recommended that the refresh interval be at least 30 seconds to avoid HTTP flood.
- Refreshing an excessive amount of courses at a time will likely cause the server to flag
  the automated browser as suspicious (and thus return an "Invalid section" error).
    - If this is the case, try disabling "Asynchronous refresh" in the settings tab.
## Libraries used
- [PyQt5](https://pypi.org/project/PyQt5/) for GUI programming
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) for web-scraping
- [Selenium](https://pypi.org/project/selenium/) to facilitate automatic login and registration
## Changelog

v1.2:
- Added a "rules" tab to facilitate switching courses.
    - The user can specify sections they are registered in so that they can be dropped before the tool registers in a section on the watch-list.
- Cleaned up requirements.txt
- Added asynchrony to section refreshes.
    - Can be toggled off in the settings tab to avoid request spam.

v1.1:
- Timer will now automatically stop if there are no more valid sections to refresh.
  


