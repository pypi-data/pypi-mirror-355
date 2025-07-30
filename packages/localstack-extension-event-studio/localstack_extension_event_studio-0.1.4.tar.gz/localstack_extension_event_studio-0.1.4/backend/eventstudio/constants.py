from typing import Set

INTERNAL_REQUEST_TRACE_HEADER = "tracing-header"
INTERNAL_CONTEXT_TRACE_CONTEXT = "_trace_context"


# Logging messages to capture internal errors and warnings
COMMON_LOG_MESSAGES_TO_CAPTURE: Set[str] = {"ErrorCode", "ErrorMessage"}
LOG_MESSAGES_TO_CAPTURE_EVENT_BRIDGE: Set[str] = {
    "InvalidArgument",
    "InternalInfoEvents at process_rules",
    "InternalInfoEvents at iterate over targets",
    "InternalInfoEvents at matches_rule",
}
LOG_MESSAGES_TO_CAPTURE = COMMON_LOG_MESSAGES_TO_CAPTURE | LOG_MESSAGES_TO_CAPTURE_EVENT_BRIDGE
