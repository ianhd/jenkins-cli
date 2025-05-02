# Jenkins CLI for Windows
Jenkins CLI for Windows is a command-line interface for deploying jobs in your Jenkins instances.

## Installation
Jenkins CLI requires [Python](https://www.python.org/) to run.

Clone this repo; install the dependencies:

```
git clone https://github.com/ianhd/jenkins-cli.git
python -m pip install python-dotenv Requests InquirerPy rich
```

Create your own `.env` file. Look at `.env.example` for a template with examples.

Create your own `jk.bat` file. Look at `jk.bat.example` for an example; modify the path inside that new `jk.bat` file to point to your `jk.py` file.

## Running the Jenkins CLI
Add `c:\Path\To\Your\jenkins-cli` to PATH. You may need to restart your command-line terminal for this to take effect.

Then, run this command:

```
jk
```