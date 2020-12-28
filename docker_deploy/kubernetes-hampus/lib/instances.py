import os
import yaml
from jinja2 import FileSystemLoader, Environment
from lib.process import run_and_inspect

from lib import ingress

TEMPLATE_PATH = "template"
TEMPLATES = [
    "subpath-deployment.yaml.jinja",
    "subpath-persistentvolumeclaim.yaml.jinja",
    "subpath-service.yaml.jinja",
]


def render_template(template_path, template, context):
    loader = FileSystemLoader(template_path)
    env = Environment(loader=loader)
    template = env.get_template(template)
    return template.render(context)


def create_instance(output_path, subpath, docker_repo, version):
    context = dict(
        SUBPATH=subpath, DOCKERREPOSITORY=docker_repo, VERSION=version, OPENTA_USE_SSL=False
    )
    full_output_path = os.path.join(output_path, subpath)
    os.makedirs(full_output_path, exist_ok=True)
    for template in TEMPLATES:
        # template_name.yaml.jinja -> template_name.yaml
        final_name, _ = os.path.splitext(template)
        with open(os.path.join(full_output_path, final_name), "w") as f:
            f.write(render_template(TEMPLATE_PATH, template, context))

def deploy_instance(instance_path, namespace):
    instance_name = os.path.basename(os.path.normpath(instance_path))
    run_and_inspect(['kubectl', 'apply', '-f', instance_path, '--namespace', namespace])
    ingress.add_route(namespace, "/{}/*".format(instance_name), instance_name, 80)