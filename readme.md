# Jenkins CLI
Jenkins CLI is a command-line interface for deploying jobs in your Jenkins instances.

## Installation
Jenkins CLI requires [Python](https://www.python.org/) to run.

Clone this repo, install the dependencies:

```
mkdir jenkins-cli
cd jenkins-cli
git clone https://github.com/ianhd/jenkins-cli.git .
pip install -r requirements.txt
```

Create your own `.env` file. Look at `.env.example` for a template with examples.

## Running the Jenkins CLI
Add `c:\Path\To\Your\jenkins-cli` to your PATH environment variable. You may need to restart your terminal for this to take effect.

In a command-line terminal, run this command:

```
jk
```