# BugCam

## Description

**BugCam** is a timelapse photogtaphy monitoring script. It checks a given Dropbox folder and alerts through a Slack Bot if it detects that an expected photo is not present in a specified period of time, or if there's an abrupt change in the picture brightness.

It is written in ``python 3``, built mainly with [Dropbox's](https://github.com/dropbox/dropbox-sdk-python) and [Slack's](https://github.com/slackapi/python-slackclient) API, [Pillow 5.2.0](https://pillow.readthedocs.io/en/latest/releasenotes/5.2.0.html), [APScheduler 3.5.3](https://apscheduler.readthedocs.io/en/latest/). (See: [requirements.txt](https://github.com/nataquinones/BugCam/blob/master/requirements.txt))

## Usage

## Tutorial

### Obtain Dropbox token
1. Log into a Dropbox account with access to the folder you want to monitor.
2. Create a new app on the [DBX Platform](https://www.dropbox.com/developers/apps/create)
  - Choose: Dropbox API
  - Choose: Full Dropbox Access
  - Name your App and click on *Create App*
3. In the My Apps menu, select your newly created app. Under the *OAuth 2 > Generated access token* section, click on *Generate*.
4. That is your token. Rename the file ``config/config_public.json`` to ``config/config.json``. Add the token in the appropriate section of the file ``config/config.json``. Keep it private.

### 2. Obtain Slack Bot token
1. Log into Slack with an account that has access to the workspace were you want the alerts to be sent.
2. Go to the [Slack API website](https://api.slack.com/apps), and select *Your Apps*.
3. Create new app by clicking *Create New App*, name app and select workspace.
4. Select the newly created app and under the menu *Features* click *Auth & Permissions*
5. Your token is the string under *Bot User OAuth Access Token*. Add it in the appropriate section of the file ``config/config.json``. Keep it private.

### 3. Define brighness thresholds
TO_DO

### 4. Run BugCam
TO_DO

