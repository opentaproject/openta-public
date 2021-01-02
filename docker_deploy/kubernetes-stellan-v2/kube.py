#!/usr/bin/env python3
import sys
import argparse
import json
from termcolor import colored
from kubernetes import client, config, watch
from kubernetes.stream import stream
from tabulate import tabulate

from lib import instances
from lib import ingress
from lib import k8parse
from lib.process import run_and_inspect

config.load_kube_config()


def get_output(api, namespace, pod, command):
    res = stream(
        api.connect_get_namespaced_pod_exec,
        pod,
        namespace,
        command=["/bin/bash", "-c", command],
        stdout=True,
        stderr=True,
        stdin=True,
        tty=True,
        container="web",
        _request_timeout=5.0,
    )
    return res


def execute_command(api, namespace, pod, command):
    res = stream(
        api.connect_get_namespaced_pod_exec,
        pod,
        namespace,
        command=["/bin/bash", "-c", command],
        stdout=True,
        stderr=True,
        stdin=True,
        tty=True,
        container="web",
        _request_timeout=1.0,
        _preload_content=False,
    )
    print(command)
    while res.is_open():
        res.update(timeout=1)
        output = False
        if res.peek_stdout():
            print("STDOUT: %s" % res.read_stdout())
            output = True
        if res.peek_stderr():
            print("STDERR: %s" % res.read_stderr())
            output = True
        if not output:
            sys.stdout.write(".")
            sys.stdout.flush()


def list_instances(args):
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(args.namespace)
    entries = []
    sys.stdout.write("Querying instances")
    sys.stdout.flush()
    for pod in pod_list.items:
        status = []
        openta_version = "unknown"
        courses = "unknown"
        disk = "unknown"
        ready_containers = k8parse.get_ready_containers_as_string(pod)
        non_ready_containers = k8parse.get_non_ready_with_reason_as_string(pod)
        if not args.quick:
            try:
                migration_status = get_output(v1, args.namespace, pod.metadata.name, "./manage.py showmigrations | grep '\[ \]' | wc -l")
                openta_version = get_output(v1, args.namespace, pod.metadata.name, "echo $OPENTA_VERSION")
                disk = get_output(v1, args.namespace, pod.metadata.name, "lsblk -o FSUSED,FSAVAIL,MOUNTPOINT | grep /srv/openta/django/backend/media | awk '{printf \"%s free (%s used)\", $2, $1}'")
                if migration_status == "0":
                    courses = get_output(v1, args.namespace, pod.metadata.name, "./manage.py list_courses")
                    courses = ", ".join(filter(len, courses.split("\n")))
                else:
                    status.append(colored("Needs migration!", "red"))
            except Exception as e:
                print("Failed to get info for pod ", pod.metadata.name)
        entries.append([
            pod.status.pod_ip, 
            pod.metadata.name, 
            openta_version, 
            courses, 
            ", ".join(status),
            disk,
            colored(ready_containers, "green"),
            colored(non_ready_containers, "red")])
        sys.stdout.write('.')
        sys.stdout.flush()
    sys.stdout.write("\n")
    print(tabulate(entries, headers=["IP", "Name", "OpenTA version", "Courses", "Status", "Media", "Ready containers", "Non-ready containers"]))

def initialize_instance(args):
    v1 = client.CoreV1Api()
    execute_command(v1, args.namespace, args.name, "./manage.py makemigrations")
    execute_command(v1, args.namespace, args.name, "./manage.py migrate")
    execute_command(v1, args.namespace, args.name, "./manage.py loaddata fixtures/auth.json")
    execute_command(v1, args.namespace, args.name, "./manage.py loaddata fixtures/course.json")
    execute_command(v1, args.namespace, args.name, "./manage.py createcachetable")


def debug_instance(args):
    v1 = client.CoreV1Api()
    pod = v1.read_namespaced_pod(name=args.name, namespace=args.namespace)
    print(pod)

def watch_instance(args):
    v1 = client.CoreV1Api()
    w = watch.Watch()
    events = w.stream(v1.list_namespaced_event, namespace=args.namespace, field_selector="involvedObject.name={}".format(args.name))
    for event in events:
        print(event['object'].first_timestamp, event['object'].message)

def watch_namespace(args):
    v1 = client.CoreV1Api()
    w = watch.Watch()
    events = w.stream(v1.list_namespaced_event, namespace=args.namespace)
    for event in events:
        print(event['object'].last_timestamp, event['object'].involved_object.name, event['object'].message)

def watch_all(args):
    v1 = client.CoreV1Api()
    w = watch.Watch()
    events = w.stream(v1.list_event_for_all_namespaces)
    for event in events:
        print(event['object'].last_timestamp, event['object'].involved_object.name, event['object'].message)

def list_deployments(args):
    print("LIST  DEPLOYMENTS ARGS = ", args )
    v1 = client.AppsV1Api()
    deployment_list = v1.list_namespaced_deployment(namespace=args.namespace)
    entries = []
    for deployment in deployment_list.items:
        entries.append([deployment.metadata.name, deployment.status])
    print(tabulate(entries, headers=["Deployment", "Status"]))

def list_data(args):
    v1 = client.CoreV1Api()
    volume_list = v1.list_namespaced_persistent_volume_claim(namespace=args.namespace)
    entries = []
    for volume in volume_list.items:
        print(volume)
        # entries.append([.metadata.name, deployment.status])
    # print(tabulate(entries, headers=["Deployment", "Status"]))


def create_instance(args):
    print("CREATE ARGS = ", args )
    instances.create_instance(args.output_path, args.subpath, args.docker_repo, args.version,args.server_info_key)

def deploy_instance(args):
    v1 = client.CoreV1Api()
    res = v1.list_namespace()
    namespaces = list(map(lambda item: item.metadata.name, res.items))
    if args.namespace not in namespaces:
        print("Creating namespace", args.namespace)
        v1.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=args.namespace)))
    instances.deploy_instance(args.instance_path, args.namespace)

def access_instance(args):
    run_and_inspect(['kubectl', 'port-forward', args.name, '{}:80'.format(args.port), '--namespace', args.namespace])

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", type=str, default="openta")
    subparsers = parser.add_subparsers()
    list_instances_parser = subparsers.add_parser("list-instances", description="test")
    list_instances_parser.add_argument("--quick", action="store_true")
    list_instances_parser.set_defaults(func=list_instances)

    list_deployments_parser = subparsers.add_parser("list-deployments")
    list_deployments_parser.set_defaults(func=list_deployments)

    list_data_parser = subparsers.add_parser("list-data")
    list_data_parser.set_defaults(func=list_data)

    create_instance_parser = subparsers.add_parser("create-instance")
    create_instance_parser.set_defaults(func=create_instance)
    create_instance_parser.add_argument("--subpath", type=str, required=True)
    create_instance_parser.add_argument("--docker-repo", type=str, required=True)
    create_instance_parser.add_argument("--version", type=str, required=True)
    create_instance_parser.add_argument("--server_info_key", type=str, required=True)
    create_instance_parser.add_argument("--output-path", type=str, required=True)

    deploy_instance_parser = subparsers.add_parser("deploy-instance")
    deploy_instance_parser.set_defaults(func=deploy_instance)
    deploy_instance_parser.add_argument("instance_path", type=str)

    debug_instance_parser = subparsers.add_parser("debug-instance")
    debug_instance_parser.set_defaults(func=debug_instance)
    debug_instance_parser.add_argument("name", type=str)

    initialize_instance_parser = subparsers.add_parser("initialize-instance")
    initialize_instance_parser.set_defaults(func=initialize_instance)
    initialize_instance_parser.add_argument("name", type=str)

    watch_instance_parser = subparsers.add_parser("watch-instance")
    watch_instance_parser.set_defaults(func=watch_instance)
    watch_instance_parser.add_argument("name", type=str)

    watch_parser = subparsers.add_parser("watch")
    watch_parser.set_defaults(func=watch_all)

    access_instance_parser = subparsers.add_parser("access-instance")
    access_instance_parser.set_defaults(func=access_instance)
    access_instance_parser.add_argument("name", type=str, help="Instance name (e.g. from list-instances)")
    access_instance_parser.add_argument("--port", type=int, default=8008, help="Local port")

    return parser.parse_args()
    # parser.add_argument("--list-instances", action='store_true')


args = parse_arguments()
if hasattr(args, 'func'):
    args.func(args)
# reinitialize_database("openta", "sandbox-946b4976b-q6pfv")
