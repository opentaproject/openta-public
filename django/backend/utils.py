def response_from_messages(messages):
    result = dict(status=set())
    result['messages'] = messages
    for msg in messages:
        result['status'].add(msg[0])
    if 'error' not in result['status']:
        result['success'] = True
    return result
