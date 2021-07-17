# UBC-Course-Scout
A Python 3.8 program with a graphical user interface to aid with UBC course registration.
## About
UBC Course Scout is a course registration tool that can automatically register for desired courses when a seat is available.
It uses web-scraping to find the number of seats for a given section, and will notify the user
or register in the course once a spot is available depending on the user's preferences.
## Notes
- In order for the auto-registration feature to take effect, the user must enter and confirm their CWL login on the settings
  tab.
- Sections added to the watch-list will be saved to disk and persist between sessions.
    - For security reasons, the user's CWL login  will NOT be saved to disk, and will need to be entered again between
  sessions.
- If the refresh timer is active and there are no more valid sections to monitor (e.g. all the sections have been successfully registered in), the refresh timer will stop automatically.
    - It recommended that the refresh interval be at least 30 seconds to avoid HTTP flood.
## Libraries used
- [PyQt5](https://pypi.org/project/PyQt5/) for GUI programming
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) for web-scraping
- [Selenium](https://pypi.org/project/selenium/) to facilitate automatic login and registration


