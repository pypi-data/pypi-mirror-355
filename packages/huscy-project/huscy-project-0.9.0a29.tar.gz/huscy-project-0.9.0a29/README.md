# Huscy

Huscy is a project to bring applications together intended for human research.

## Requirements

You'll need the OpenLDAP libraries and headers available on your system.

```
sudo apt install libldap2-dev libsasl2-dev
```

## Getting started

Huscy works with [Python 3.6](https://www.python.org/downloads/), on any platform.

To get started with Huscy, run the following in a virtual environment:

```
pip install huscy-project
huscy start <project_name>
cd <project_name>
python manage.py migrate
python manage.py runserver
```

## Security

We take the security of Huscy, and related packages we maintain, seriously. If you have found a security issue with any of our projects please email us at huscy@cbs.mpg.de so we can work together to find and patch the issue. We appreciate responsible disclosure with any security related issues, so please contact us first before creating a Bitbucket issue.
