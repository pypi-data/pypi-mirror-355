# HEA Server Settings Microservice
[Research Informatics Shared Resource](https://risr.hci.utah.edu), [Huntsman Cancer Institute](https://healthcare.utah.edu/huntsmancancerinstitute/),
Salt Lake City, UT

The HEA Server Settings Microservice manages user and system settings.

## Version 1.3.1
* Bumped heaserver version to 1.32.1.
* The super_admin_default_permissions attribute is now an empty list.


## Version 1.3.0
* Bumped heaserver version to 1.30.1.
* Removed CREATOR from permissions dropdowns in the properties metadata.
* Added missing type attribute metadata to shares in the properties metadata.

## Version 1.2.1
* Bumped heaserver version to 1.28.1.

## Version 1.2.0
* Added support for python 3.12.
* Added group permissions support.

## Version 1.1.0
* Make settings show based on permissions.
* Make Credentials settings object expect CredentialsView actual objects.
* Remove integration tests because they are duplicative.

## Version 1
* Initial release.

## Runtime requirements
* Python 3.10, 3.11, or 3.12.

## Development environment

### Build requirements
* Any development environment is fine.
* On Windows, you also will need:
    * Build Tools for Visual Studio 2019, found at https://visualstudio.microsoft.com/downloads/. Select the C++ tools.
    * git, found at https://git-scm.com/download/win.
* On Mac, Xcode or the command line developer tools is required, found in the Apple Store app.
* Python 3.10-3.12: Download and install Python from https://www.python.org, and select the options to install
for all users and add Python to your environment variables. The install for all users option will help keep you from
accidentally installing packages into your Python installation's site-packages directory instead of to your virtualenv
environment, described below.
* Create a virtualenv environment using the `python -m venv <venv_directory>` command, substituting `<venv_directory>`
with the directory name of your virtual environment. Run `source <venv_directory>/bin/activate` (or `<venv_directory>/Scripts/activate` on Windows) to activate the virtual
environment. You will need to activate the virtualenv every time before starting work, or your IDE may be able to do
this for you automatically. **Note that PyCharm will do this for you, but you have to create a new Terminal panel
after you newly configure a project with your virtualenv.**
* From the project's root directory, and using the activated virtualenv, run `pip install wheel` followed by
  `pip install -r requirements_dev.txt`. **Do NOT run `python setup.py develop`. It will break your environment.**

### Running tests
Run tests with the `pytest` command from the project root directory. To improve performance, run tests in multiple
processes with `pytest -n auto`.

### Running integration tests
* Install Docker
* On Windows, install pywin32 version >= 223 from https://github.com/mhammond/pywin32/releases. In your venv, make sure that
`include-system-site-packages` is set to `true`.

### Trying out the APIs
This microservice has Swagger3/OpenAPI support so that you can quickly test the APIs in a web browser. Do the following:
* Install Docker, if it is not installed already.
* Run the `run-swaggerui.py` file in your terminal. This file contains some test objects that are loaded into a MongoDB
  Docker container.
* Go to `http://127.0.0.1:8080/docs` in your web browser.

Once `run-swaggerui.py` is running, you can also access the APIs via `curl` or other tool. For example, in Windows
PowerShell, execute:
```
Invoke-RestMethod -Uri http://localhost:8080/components/ -Method GET -Headers @{'accept' = 'application/json'}`
```
In MacOS or Linux, the equivalent command is:
```
curl -X GET http://localhost:8080/components/ -H 'accept: application/json'
```


### Packaging and releasing this project
See the [RELEASING.md](RELEASING.md) file for details.
