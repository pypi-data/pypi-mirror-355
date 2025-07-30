from enum import Enum
from collections import defaultdict
from kopf import Patch, timer, on
from pydantic import BaseModel, Field
import requests
from kubernetes import client, config
from justernetes.logging import logger
from justernetes.settings import settings
from threading import Timer


RESOURCE = 'justniffers.knspar.github.io'
CRD_GROUP = 'knspar.github.io'
CRD_VERSION = 'v1'
CRD_PLURAL = 'justniffers'
STATUS_ANNOTATION = 'status'

class Phase(Enum):
    PENDING = 'Pending'
    UPDATING = 'Updating'
    RUNNING = 'Running'
    FAILED = 'Failed'
    DELETING = 'Deleting'
    STOPPED = 'Stopped'


def post(url, **kwargs):
    logger.debug(f'POST {url} {kwargs}')
    return requests.post(url, **kwargs)


def get(url, **kwargs):
    logger.debug(f'GET {url} {kwargs}')
    return requests.get(url, **kwargs)


class Condition(BaseModel):
    lastTransitionTime: str | None = None
    message: str | None = None
    reason: str | None = None
    status: str | None = None
    type: str | None = None


class Status(BaseModel):
    phase: str | None = None
    conditions: list[Condition] = Field(default_factory=list)


class Spec(BaseModel):
    filter: str | None = None
    interface: str | None = None
    log_format: str | None = None
    max_tcp_streams: int | None = None
    truncated: bool = False
    newline: bool = False
    in_the_middle: bool = True
    encode: str | None = None
    active: bool = True


class Metadata(BaseModel):
    annotations: dict[str, str] = Field(default_factory=dict)
    generation: int
    name: str
    namespace: str
    resourceVersion: str
    uid: str


class JustnifferCRD(BaseModel):
    apiVersion: str
    kind: str
    metadata: Metadata
    spec: Spec
    status: Status | None = None


@on.create(RESOURCE)  # type: ignore
def create_handler(body, patch: Patch, **kwargs):
    logger.debug(f'Created Justniffer {body["metadata"]["name"]}')
    logger.debug(f'Created Justniffer {body=}')
    justniffer_crd = JustnifferCRD.model_validate(body)
    patch.status['phase'] = Phase.PENDING.value
    debounce_update_services()
    logger.debug(f'Created Justniffer {justniffer_crd.metadata.name} {justniffer_crd=}')


@on.update(RESOURCE)  # type: ignore
def update_handler(body,  patch: Patch,  **kwargs):
    for k, v in kwargs.items():
        logger.info(f'Updated Justniffer {body["metadata"]["name"]} {k} {type(v)}')
    logger.info(f'Updated Justniffer {body["metadata"]["name"]} fico')
    patch.status['phase'] = Phase.UPDATING.value

    debounce_update_services()


@on.delete(RESOURCE)  # type: ignore
def delete_handler(body, **kwargs):
    logger.debug(f'Deleting Justniffer {body["metadata"]["name"]}')

    config.load_config()
    api = client.CustomObjectsApi()

    namespace = body['metadata']['namespace']
    name = body['metadata']['name']

    status_update = {
        'status': {
            'phase': Phase.DELETING.value
        }
    }

    try:
        response = api.patch_namespaced_custom_object_status(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=namespace,
            plural=CRD_PLURAL,
            name=name,
            body=status_update
        )
        logger.debug(f'Updated Justniffer {name} status to Deleting. API response: {response}')
        debounce_update_services()
    except Exception as e:
        logger.error(f'Failed to update status for {name}: {e}')


@on.startup()
def startup(*args, **kwargs):
    logger.debug(f'Justniffer CRD initialized {args} {kwargs}')
    debounce_update_services()


update_services_timer = None


def mocked_update_services():
    logger.debug(f'Justniffer mocked_update_services CRD mocked ')


def debounce_update_services(delay=5):
    global update_services_timer
    if update_services_timer:
        update_services_timer.cancel()
    update_services_timer = Timer(delay, update_services)
    update_services_timer.start()


def equal_to_the_first_dict(d1: dict, d2: dict) -> bool:
    comparison_result = [d1[key] == d2.get(key) for key in d1]
    return all(comparison_result)


def update_services():
    config.load_config()
    api = client.CustomObjectsApi()

    l = api.list_cluster_custom_object(CRD_GROUP, CRD_VERSION, CRD_PLURAL)

    justniffer_proxy_endpoint = settings.justniffer_proxy_endpoint
    headers = {'X-API-Key': settings.justniffer_proxy_api_key}

    all_matching = False
    res = get(f'{justniffer_proxy_endpoint}/list', headers=headers)
    running_definitions = defaultdict(lambda:defaultdict(lambda: False))
    tot_procs = 0
    supposed_proc = 0
    if res.status_code == 200:
        instance_list = res.json()
        supposed_proc = len([e for e in l['items'] if e['spec'].get('active', True)])*len(instance_list)
        tot_procs = sum(map(lambda p:len(p.get('processes',{})), instance_list))
        for idx, def_obj in enumerate(l['items']):
            s = JustnifferCRD.model_validate(def_obj).spec
            d1 = s.model_dump()
            if 'active' in d1:
                del d1['active']
            for idx_instance , instance_status in enumerate(instance_list):
                found = False
                for process in instance_status.get('processes', {}).values():
                    running = process['justniffer_spec']
                    if equal_to_the_first_dict(d1, running):
                        found = True
                if s.active:
                    running_definitions[idx][idx_instance] = found 
                else:
                    running_definitions[idx][idx_instance] = not found 
    all_matching = all([value for inner_dict in running_definitions.values() for value in inner_dict.values()]) and supposed_proc == tot_procs
    logger.debug(f'All matching: {all_matching} {running_definitions}')
    phase = Phase.STOPPED.value
    if not all_matching:
        res = post(f'{justniffer_proxy_endpoint}/stop-all', headers=headers)
        logger.debug(f'Stopped all services. Response: {res.status_code}')

        for i in l['items']:
            j = JustnifferCRD.model_validate(i)
            if j.status is None or j.status.phase == Phase.DELETING.value:
                logger.debug(f'Justniffer {j.metadata.name} is being deleted or has no status.')
                continue
            if  j.spec.active:
                req = j.spec.model_dump()
                del req['active']
                res = post(f'{justniffer_proxy_endpoint}/start', json=req, headers=headers)
                instance_status = res.json()

                uuids = list(filter(lambda e: e, map(lambda e: e.get('uuid'), instance_status)))
                errors = list(filter(lambda e: e, map(lambda e: e.get('message'), instance_status)))

                phase = ''
                message_content = ''

                if len(uuids) == 0:
                    phase = Phase.FAILED.value
                    message_content = ' '.join(errors)
                    logger.error(f'Justniffer {j.metadata.name} failed to start: {message_content}')
                else:
                    phase = Phase.RUNNING.value
                    message_content = ' '.join(uuids) + ' '.join(errors)
                    logger.info(f'Justniffer {j.metadata.name} is running with UUIDs: {" ".join(uuids)}')

            status_update = {
                'status': {
                    'phase': phase
                }
            }

            namespace = j.metadata.namespace
            name = j.metadata.name
            try:
                response = api.patch_namespaced_custom_object_status(
                    group=CRD_GROUP,
                    version=CRD_VERSION,
                    namespace=namespace,
                    plural=CRD_PLURAL,
                    name=name,
                    body=status_update
                )
                logger.debug(f'Updated Justniffer {name} status. API response: {response}')
            except Exception as e:
                logger.error(f'Failed to patch status for Justniffer {name}: {e}')


def get_api() -> client.CoreV1Api:
    config.load_config()
    return client.CoreV1Api()


@timer(RESOURCE, interval=settings.check_interval)  # type: ignore
def timer_handler(body, **kwargs):
    justniffer_crd = JustnifferCRD.model_validate(body)
    logger.debug(f'Timer triggered for Justniffer {justniffer_crd.metadata.name}')
    debounce_update_services()


def test_update_services():
    update_services()
