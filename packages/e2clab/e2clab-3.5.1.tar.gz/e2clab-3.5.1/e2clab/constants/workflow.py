"""Workflow file constants"""

TARGET = "hosts"
DEPENDS_ON = "depends_on"
SERV_SELECT = "service_selector"
GROUPING = "grouping"
PREFIX = "prefix"
SELF_PREFIX = "_self"

WORKFLOW_GROUPING_LIST = [
    "round_robin",
    "asarray",
    "aggregate",
    # used internally by e2clab, not meant to use for the user
    "address_match",
]

GROUPING_LIST_USER = [
    "round_robin",
    "asarray",
    "aggregate",
    "address_match",
]

ARRAY_INFO = "array_info"
ARRAY_INFO_ENUM = ["id", "hostname", "g5k_ipv6_hostname"]

DEFAULT_GROUPING = "round_robin"

ANSIBLE_TASKS = "tasks"

WORKFLOW_DEVICE_TASK = ["copy", "shell", "fetch"]
