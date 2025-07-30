"""Constants used in the project."""

SENSITIVE_TOOLS_RESOURCE_PATH = "tools://sensitive"

UNKNOWN = "Unknown"

MACHINE_REGISTRATION_STATE = {
    0: "Unkown",
    1: "Registered",
    2: "Unregistered",
}

MACHINE_LIFECYCLE_STATE = {
    0: "Active",
    1: "Deleted",
    2: "Require Resolusion",
    3: "Stub",
}

MACHINE_POWER_STATE = {
    0: "Unknown",
    1: "Unavailable",
    2: "Off",
    3: "On",
    4: "Suspended",
    5: "Turning On",
    6: "Turning Off",
    7: "Suspending",
    8: "Resuming",
    9: "Unmanaged",
    10: "Not Supported",
    11: "Virtual Machine Not Found",
}

MACHINE_FAULT_STATE = {
    0: "Unknown",
    1: "None",
    2: "Failed to Start",
    3: "Stuck on Boot",
    4: "Unregistered",
    5: "Max Capacity",
}

MACHINE_ROLE = {
    0: "VDA",
    1: "DDC",
    2: "Both",
}
