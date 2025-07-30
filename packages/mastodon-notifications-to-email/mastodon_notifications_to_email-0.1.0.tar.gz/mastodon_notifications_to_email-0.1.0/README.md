# Mastodon Notifications To Email

Send Mastodon/GoToSocial notifications as emails.

The generated emails look similar to the notification emails sent by Mastodon.
Some Mastodon-like platform implementations like GoToSocial do not send notifications
via email by itself and then this small script comes into play.

It can be used as cronjob or long running process, e.g. with Systemd or in a Docker container.

## Installation and setup

mastodon_notifications_to_email requires Python 3.11 or newer.
The easiest method is to install directly from pypi using pip:

    pip install mastodon-notifications-to-email

Dependencies:
  - Mastodon.py
  - markdownify

Alternatively, you can skip installation and just execute the script:

    uv run mastodon_notifications_to_email

Before using mastodon_notifications_to_email, you need to create a configuration file called
`mastodon_notifications_to_email.conf`. mastodon_notifications_to_email will search
for the file in the following locations (in that order):

  - ~/.config/mastodon_notifications_to_email.conf
  - mastodon_notifications_to_email.conf (in current working directory)

An example configuration file can be found in the sources or online
at https://codeberg.org/eht16/mastodon_notifications_to_email/raw/branch/master/mastodon_notifications_to_email.conf.example.

For details on the configuration options, consider the comments in the
example configuration file.

## Usage

Run only once (e.g. as cronjob):

    mastodon_notifications_to_email

Run in foreground:

    mastodon_notifications_to_email -f

### Command line options

    usage: mastodon_notifications_to_email.py [-h] [-v] [-f] [-c FILE]

    options:
      -h, --help         show this help message and exit
      -v, --verbose      Show more log messages (default: False)
      -f, --foreground   Keep running in foreground (default: False)
      -c, --config FILE  configuration file path (default: None)

## Disclaimer

Use this tool at your own risk only.
There is no warranty at all.

## Author

Enrico Tröger <enrico.troeger@uvena.de>
