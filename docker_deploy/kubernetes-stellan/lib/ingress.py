from kubernetes import client

INGRESS_NAME = "openta-ingress"

def get_ingress(namespace):
    net_api = client.NetworkingV1beta1Api()
    ingress = net_api.read_namespaced_ingress(INGRESS_NAME, namespace)
    return ingress

def add_route(namespace, path, service_name, service_port):
    net_api = client.NetworkingV1beta1Api()
    ingress = net_api.read_namespaced_ingress(INGRESS_NAME, namespace)
    ingress.spec.rules.append(client.NetworkingV1beta1IngressRule(
                http=client.NetworkingV1beta1HTTPIngressRuleValue(
                    paths=[client.NetworkingV1beta1HTTPIngressPath(
                        path=path,
                        backend=client.NetworkingV1beta1IngressBackend(
                            service_port=service_port,
                            service_name=service_name)

                    )]
                )))
    new_ingress = net_api.patch_namespaced_ingress(INGRESS_NAME, namespace, ingress)
    return new_ingress.spec.rules

def remove_route(namespace, service_name):
    net_api = client.NetworkingV1beta1Api()
    ingress = net_api.read_namespaced_ingress(INGRESS_NAME, namespace)
    ingress.spec.rules = list(filter(lambda rule: rule.http.paths[0].backend.service_name != service_name, ingress.spec.rules))
    new_ingress = net_api.patch_namespaced_ingress(INGRESS_NAME, namespace, ingress)
    return new_ingress.spec.rules

