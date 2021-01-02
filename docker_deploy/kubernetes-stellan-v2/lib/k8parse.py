def get_non_ready_containers(pod):
    if pod.status.container_statuses is not None:
        return filter(lambda item: not item.ready, pod.status.container_statuses)
    else:
        return []

def get_non_ready_with_reason_as_string(pod):
    return ", ".join(list(
                map(lambda item: "{name} ({reason})".format(
                    name=item.name, 
                    reason=item.state.waiting.reason
                ),
                get_non_ready_containers(pod))))

def get_ready_containers_as_string(pod):
    if pod.status.container_statuses is not None:
        return ", ".join(list(
                map(lambda item: item.name, 
                filter(lambda item: item.ready, pod.status.container_statuses))))
    else:
        return ""