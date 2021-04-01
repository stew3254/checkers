# Checkers

A simple web server to play checkers, and an AI to play against.

### Running
These instructions will cover both the PyCharm steps, and the command line steps

For both, `git clone https://github.com/stew3254/checkers.git` the repo

If running in PyCharm do the following:
1. Open this in PyCharm and go to `settings -> project -> project interpreter` press the settings wheel and hit add, then create a virtual environment for this project
1. Install the requirements for this project (There should be a button up on the top somewhere)
    1. If not, follow steps 2 and 3 in the command line setup to fix this
1. Create a new flask configuration
   1. Hit the dropdown next to the run button
   1. Click edit configurations
   1. Click the plus button in the top left and select flask server
   1. Make sure the project interpreter is the virtual environment created for this project and hit okay
1. Click the run button.

If running through the command line, follow these steps.
1. Create a new virtual environment by running `python3 -m venv venv`
1. Source the virtual env `source venv/bin/activate`
1. Now run `pip install -r requirements.txt` to install the requirements
1. Run `python app.py`

The flask app and have it open to http://localhost:5000