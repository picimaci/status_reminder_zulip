import os
import zulip
import unidecode
import re
from datetime import datetime


no_status_needed = os.environ['NO_STATUS_NEEDED']
alternative_names = os.environ['ALTERNATIVE_NAMES']
stream = os.environ['ZULIP_STREAM']
topic = os.environ['ZULIP_TOPIC']
# ZULIP_SITE - zulip client
# ZULIP_EMAIL - zulip client
# ZULIP_API_KEY - zulip client


client = zulip.Client()


def normalize_string(input):
    return unidecode.unidecode(input).lower()


def get_todays_off_bot_message():
    # zulip update utan ezt a requestet updatelni kell
    request = {
        'anchor': 10000000000000000,
        'num_before': 1,
        'num_after': 0,
        'narrow': [{'operator': 'sender', 'operand': 'off-bot@zulip.wanari.net'},
                   {'operator': 'stream', 'operand': 'Off'}],
    }
    result = client.get_messages(request)
    messages = result.get('messages', [])
    return str(next(iter(messages), {}).get('content'))


def process_off_message(message):
    on_vacation = [normalize_string(x) for x in re.findall('<li>(.*) szabin', message)]
    not_working_lines = re.findall('Nem dolgozik: (.*), </li>', message)
    not_working = list(normalize_string(x.strip()) for x in next(iter(not_working_lines), '').split(','))
    return on_vacation + not_working


# Kiszurjuk azokat, akik nem irnak statuszt
# "is_bot": false,
# "is_active": true,
def filter_member(member):
    return not member.get('is_bot', True) and member.get('is_active', False)


def get_users_writing_status():
    all_members = list(filter(filter_member, client.get_members().get('members', [])))
    all_names = list([normalize_string(x.get('full_name')), x.get('full_name')] for x in all_members)

    def filter_for_status_needed(member):
        return member[0] not in (no_status_needed + outsource)

    status_needed_members = list(filter(filter_for_status_needed, all_names))

    return status_needed_members


def filter_message_for_date(message):
    timestamp = message.get('timestamp', 0)
    return datetime.today().date() == datetime.fromtimestamp(timestamp).date()


def get_todays_status_messages():
    # zulip update utan ezt a requestet updatelni kell

    # egyelore nincs date support message fetcheleshez, igy atmeneti megoldaskent az utolso 30 uzenetet lekerjuk,
    # es aztan szurunk a datumra
    request = {
        'anchor': 10000000000000000,
        'num_before': 30,
        'num_after': 0,
        'narrow': [{'operator': 'topic', 'operand': topic},
                   {'operator': 'stream', 'operand': stream}],
    }
    result = client.get_messages(request)
    return list(filter(filter_message_for_date, result.get('messages', [])))


def get_wrote_status(status_messages):
    senders = set(x.get('sender_full_name', '') for x in status_messages)
    return list(normalize_string(x) for x in senders)


def get_outsource(status_messages):
    def filter_outsource(message):
        return ':outbox:' in message.get('content', '')

    outsource_message = list(filter(filter_outsource, status_messages))[-1].get('content', '')
    outsource = [normalize_string(x) for x in re.findall('\n- (.*): ', outsource_message)]
    return outsource


def send_message_to_status_stream(people_to_remind):
    content = "status reminder - " + ' '.join(list('@**' + x + '**' for x in people_to_remind))
    request = {
        "type": "stream",
        "to": stream,
        "topic": topic,
        "content": content,
    }
    client.send_message(request)


def get_people_that_need_reminding(done_people, all_people):
    def filter_for_status_reminder(member):
        return member[0] not in done_people

    people_to_remind = list(filter(filter_for_status_reminder, all_people))
    return (x[1] for x in people_to_remind)


todays_off_message = get_todays_off_bot_message()
absentees = process_off_message(todays_off_message)
status_messages = get_todays_status_messages()
wrote_status = get_wrote_status(status_messages)
outsource = get_outsource(status_messages)
users_writing_status = get_users_writing_status()
status_done = absentees + wrote_status
status_done_names_corrected = list(name.replace(name, alternative_names.get(name, name)) for name in status_done)

need_reminding = list(get_people_that_need_reminding(status_done_names_corrected, users_writing_status))

send_message_to_status_stream(need_reminding)
