def new_mailing_message_parser(message):
    lst = message.lstrip('/new_mailing').replace(']\n[', '][').strip().lstrip('[').rstrip(']').split('][')
    post_text = None
    button_text = None
    button_event_for_subscribers = None
    button_event_for_no_subscribers = None
    condition = None
    for i in lst:
        if 'POST_TEXT::' in i:
            post_text = i.split('::')[-1]
        elif 'BUTTON_TEXT::' in i:
            button_text = i.split('::')[-1]
        elif 'NO_SUB_EVENT::' in i:
            button_event_for_no_subscribers = i.split('::')[-1]
        elif 'SUB_EVENT::' in i:
            button_event_for_subscribers = i.split('::')[-1]
        elif 'COND::' in i:
            condition = i.split('::')[-1]
    if button_text is not None:
        if button_event_for_no_subscribers is None and button_event_for_subscribers is not None:
            button_event_for_no_subscribers = button_event_for_subscribers
        elif button_event_for_subscribers is None:
            button_event_for_no_subscribers, button_event_for_subscribers = 'None', 'None'
    return {
        'POST_TEXT': post_text,
        'BUTTON_TEXT': button_text,
        'SUB_EVENT': button_event_for_subscribers,
        'NO_SUB_EVENT': button_event_for_no_subscribers,
        'COND': condition,
    }

