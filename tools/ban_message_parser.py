import datetime


def ban_message_parser(message):
    lst = message.lstrip('/new_mailing').replace(']\n[', '][').strip().lstrip('[').rstrip(']').split('][')
    time = None
    reason = None
    for i in lst:
        if 'TIME::' in i:
            time = i.split('::')[-1]
        elif 'REASON::' in i:
            reason = i.split('::')[-1]
    res = {}
    res['time'] = datetime.datetime.now().timestamp() + int(time) * 60 * 60 * 24
    res['days'] = time
    res['reason'] = reason
    return res