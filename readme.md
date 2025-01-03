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
In a command-line, like Windows PowerShell, make sure you are currently in the `jenkins-cli` directory. You can then run `python jk.py`. Alternatively (and recommended!), you can run the `jk` command directly. In order to do that, you can create a function. In PowerShell, this is how you do that:

```
notepad $PROFILE
```

Enter in the following, changing the path as needed, then save and close notepad:

```
function jk {
    python "C:\projects\jenkins-cli\jk.py" $args
}
```

Then run this command to update:

```
. $PROFILE
```

Now, you can simply run the `jk` command.

```
jk
```