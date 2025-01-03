# Jenkins CLI
Jenkins CLI is a command-line interface for deploying jobs in your Jenkins instances.

## Installation
Jenkins CLI requires [Python](https://www.python.org/) to run. I built it on a Windows machine and use it with [Windows PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4#install-powershell-using-winget-recommended).

Clone this repo, install the dependencies:

```
mkdir jenkins-cli
cd jenkins-cli
git clone https://github.com/ianhd/jenkins-cli.git .
pip install -r requirements.txt
```

Create your own `.env` file. Look at `.env.example` for a template with examples.

## Running the Jenkins CLI
In a command-line, like Windows PowerShell, make sure you are currently in the `jenkins-cli` directory. Then run this command:

```
jk
```