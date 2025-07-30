#!/usr/bin/env python3
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from configparser import ConfigParser
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import logging
import logging.handlers
from pathlib import Path
import smtplib
import sqlite3
from time import sleep

import markdownify
from mastodon import Mastodon


CONFIG_FILENAME = '~/.config/mastodon_notifications_to_email.conf'
MAIL_MESSAGE_TEMPLATE = '''Hi {username},

{message}
{status}

---

Their account:   {their_url}
Your account:    {user_url}
Your instance:   {instance}
Notification ID: {notification_id}
Sent to you by mastodon_notifications_to_email.py (https://codeberg.org/eht16/mastodon_notifications_to_email)
'''

DATABASE_SCHEMA_STATEMENTS = [
    '''
    CREATE TABLE IF NOT EXISTS `notification` (
      `notification_id` TEXT NOT NULL PRIMARY KEY
    );
    ''',
]

__version__ = 1.0


class StopFetchLoopError(Exception):
    pass


class MastodonNotificationEmailProcessor:

    def __init__(self, config_file_path, run_in_foreground, verbose):
        self._config_file_path = config_file_path
        self._run_in_foreground = run_in_foreground
        self._verbose = verbose
        self._config = None
        self._logger = None
        self._instance = None
        self._access_token = None
        self._timeout = None
        self._check_interval = None
        self._database_path = None
        self._lock_file_path = None
        self._mail_from = None
        self._mail_recipient = None
        self._mail_server_hostname = None
        self._mail_server_port = None
        self._api_client = None
        self._user = None
        self._database_connection = None

    def process(self):
        self._setup_config()
        self._setup_logger()
        self._log_hello()
        self._assert_not_already_running()
        self._write_lock()
        self._setup_api_client()
        self._setup_database()

        try:
            while True:
                self._user = self._api_client.me()

                for notification in self._api_client.notifications(limit=80):
                    self._process_notification(notification)

                self._wait_for_next_check_interval()
        except (StopFetchLoopError, KeyboardInterrupt):
            pass
        finally:
            self._remove_lock()
            self._close_database()

        self._log_farewell()

    def _setup_config(self):
        config_parser = ConfigParser(allow_no_value=True, delimiters=('=',))
        # read config file from location as specified via command line but fail it if doesn't exist
        if self._config_file_path:
            with Path(self._config_file_path).open('r', encoding='utf-8') as config_file_h:
                config_parser.read_file(config_file_h)

        # otherwise try pre-defined config file locations
        else:
            config_file_paths = (
                Path(CONFIG_FILENAME).expanduser(),
                'mastodon_notifications_to_email.conf'
            )
            config_parser.read(config_file_paths)

        self._instance = config_parser.get('settings', 'instance')
        self._access_token = config_parser.get('settings', 'access_token')
        self._timeout = config_parser.getfloat('settings', 'timeout', fallback=60)
        self._check_interval = config_parser.getfloat('settings', 'check_interval', fallback=3600)
        self._database_path = Path(config_parser.get('settings', 'database_path'))
        self._lock_file_path = Path(config_parser.get('settings', 'lock_file_path'))
        self._mail_from = config_parser.get('settings', 'mail_from')
        self._mail_recipient = config_parser.get('settings', 'mail_recipient')
        self._mail_server_hostname = config_parser.get('settings', 'mail_server_hostname')
        self._mail_server_port = config_parser.getint('settings', 'mail_server_port')

    def _setup_logger(self):
        log_level = logging.DEBUG if self._verbose else logging.WARN
        me = Path(__file__).name
        log_format = '%(asctime)s [%(levelname)+8s] [%(process)-8s] [%(name)-30s] %(message)s'
        logging.basicConfig(format=log_format, level=log_level)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)

        self._logger = logging.getLogger(me)

    def _assert_not_already_running(self):
        if self._lock_file_path.exists():
            msg = 'Already running. Aborting.'
            self._logger.info(msg)
            raise RuntimeError(msg)

    def _write_lock(self):
        self._lock_file_path.touch()

    def _setup_api_client(self):
        self._api_client = Mastodon(
            api_base_url=self._instance,
            access_token=self._access_token,
            request_timeout=self._timeout,
        )

    def _setup_database(self):
        self._database_connection = sqlite3.connect(
            self._database_path,
            isolation_level='EXCLUSIVE')
        self._database_connection.row_factory = sqlite3.Row
        # initialize schema
        try:
            for statement in DATABASE_SCHEMA_STATEMENTS:
                self._database_connection.execute(statement)
        except sqlite3.OperationalError:
            self._close_database()
            raise

    def _log_hello(self):
        self._logger.info('Starting...')

    def _log_farewell(self):
        self._logger.info('Finished.')

    def _process_notification(self, notification):  # noqa: C901
        if self._notification_exists(notification.id):
            return

        name = notification.account.acct

        match notification.type:
            case 'favourite':
                subject = f'{name} favorited your post'
                message = f'Your post was favorited by {name}:'
            case 'follow':
                subject = f'{name} is now following you'
                message = f'{name} is now following you!'
            case 'follow_request':
                subject = f'Pending follower: {name}'
                message = f'{name} has requested to follow you'
            case 'mention':
                subject = f'You were mentioned by {name}'
                message = f'You were mentioned by {name} in:'
            case 'poll':
                subject = f'A poll by {name} has ended'
                if notification.account.id == self._user.id:
                    message = 'Your poll has ended:'
                else:
                    message = 'A poll you voted in has ended:'
            case 'reblog':
                subject = f'{name} boosted your post'
                message = f'Your post was boosted by {name}:'
            case 'status':
                subject = f'{name} just posted'
                message = f'New post published by {name}:'
            case 'update':
                subject = f'{name} edited a post:'
                message = f'A post was edited by {name}:'
            case _:
                subject = f'New notification from {name}'
                message = f'Unhandled notification type "{notification.type}:\n\n' \
                          f'{notification.to_json()}'
                notification.status = None  # remove status as it is dumped already in `message`

        mail_text = self._factor_mail_message(message, notification)
        self._send_mail(subject, mail_text, notification.created_at, notification.id)
        self._store_notification(notification.id)
        self._logger.debug(
            'Processed new notification: id="%s", type="%s", name="%s"',
            notification.id,
            notification.type,
            name,
        )

    def _notification_exists(self, notification_id):
        query = 'SELECT 1 FROM `notification` WHERE `notification_id`=?;'
        result = self._database_connection.execute(query, (notification_id,))
        return result.fetchone() is not None

    def _factor_mail_message(self, message, notification):
        status_text = self._factor_status_text(notification)

        mail_message = MAIL_MESSAGE_TEMPLATE.format(
            username=self._user.display_name or self._user.acct,
            user_url=self._user.url,
            their_url=notification.account.url,
            message=message,
            status=status_text,
            notification_id=notification.id,
            instance=self._instance)
        return mail_message

    def _factor_status_text(self, notification):
        status_text = ''
        if notification.status:
            quoted_status_text = ''
            status_text = markdownify.markdownify(
                notification.status.content,
                strip=['a'],
                escape_misc=False,
                escape_asterisks=False,
                escape_underscores=False).strip()
            if poll_text := self._factor_poll_text(notification):
                status_text = f'{status_text}{poll_text}'

            for line in status_text.splitlines():
                quoted_status_text = f'{quoted_status_text}\n> {line}'

            status_text = f'''{quoted_status_text}\n\nView: {notification.status.url}\n'''

        return status_text

    def _factor_poll_text(self, notification):
        if poll := notification.status.poll:
            if poll.expires_at:
                expires_at = poll.expires_at.strftime('%c %Z')
            else:
                expires_at = '<unset>'

            poll_text = f'\n\nPoll ({poll.votes_count} votes so far, expires at {expires_at}):\n'
            for option in poll.options:
                poll_text += f'[ ] {option["title"]} ({option["votes_count"]} votes so far)\n'

            return poll_text

        return ''

    def _send_mail(self, subject, message, date, notification_id):
        msg = MIMEText(message, _charset='utf-8')

        recipients = [self._mail_recipient]
        msg['From'] = self._mail_from
        msg['To'] = COMMASPACE.join(recipients)
        msg['Date'] = formatdate(date.timestamp())
        msg['Subject'] = subject
        msg.add_header('X-Notification-Id', f'{notification_id}')

        smtp = smtplib.SMTP(self._mail_server_hostname, self._mail_server_port)
        smtp.sendmail(self._mail_recipient, recipients, msg.as_string())
        smtp.quit()

    def _store_notification(self, notification_id):
        query = 'INSERT INTO `notification` (`notification_id`) VALUES (?)'
        self._database_connection.execute(query, (notification_id,))
        self._database_connection.commit()

    def _wait_for_next_check_interval(self):
        if not self._run_in_foreground:
            # raise a dedicated exception to break the while(true) loop in self.process()
            raise StopFetchLoopError

        self._logger.debug('Sleeping for %s seconds', self._check_interval)
        sleep(self._check_interval)

    def _remove_lock(self):
        self._lock_file_path.unlink()

    def _close_database(self):
        if self._database_connection is not None:
            self._database_connection.close()
            self._database_connection = None


def main():
    argument_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        help='Show more log messages',
        default=False)
    argument_parser.add_argument(
        '-f',
        '--foreground',
        dest='foreground',
        action='store_true',
        help='Keep running in foreground')
    argument_parser.add_argument(
        '-c',
        '--config',
        dest='config_file_path',
        metavar='FILE',
        help='configuration file path')

    arguments = argument_parser.parse_args()

    processor = MastodonNotificationEmailProcessor(
        arguments.config_file_path,
        arguments.foreground,
        arguments.verbose)
    processor.process()


if __name__ == '__main__':
    main()
