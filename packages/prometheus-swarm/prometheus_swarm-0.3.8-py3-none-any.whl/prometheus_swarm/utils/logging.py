"""Centralized logging configuration and utilities."""

import logging
import sys
import traceback
from typing import Any, Callable, Optional, Dict
from pathlib import Path
from functools import wraps
import ast
from colorama import init, Fore, Style
import contextvars

# Initialize colorama for cross-platform color support
init(strip=False)  # Force color output even when not in a terminal

# Create our logger
logger = logging.getLogger("builder")
logger.setLevel(logging.INFO)
# Prevent propagation to avoid duplicate logs
logger.propagate = False

# Track if logging has been configured
_logging_configured = False

# Optional external error hook
_external_error_logging_hook: Optional[
    Callable[
        [
            Exception,
            str,
            str,
            Optional[str],
            Optional[str],
            Optional[str],
            Optional[str],
        ],
        None,
    ]
] = None

# Optional external logging hook
_external_logging_hook: Optional[
    Callable[
        [str, str, Optional[str], Optional[str], Optional[str], Optional[str]], None
    ]
] = None

# Optional conversation hook
_conversation_hook: Optional[
    Callable[[str, str, Any, str, Dict[str, Any], str], None]
] = None

# Context variables
task_id_var = contextvars.ContextVar("task_id", default=None)
swarm_bounty_id_var = contextvars.ContextVar("swarm_bounty_id", default=None)
todo_uuid_var = contextvars.ContextVar("todo_uuid", default=None)
signature_var = contextvars.ContextVar("signature", default=None)
conversation_context_var = contextvars.ContextVar("conversation_context", default={})


class SectionFormatter(logging.Formatter):
    """Custom formatter that only shows timestamp and level for section headers and errors."""

    def format(self, record):
        # Check if this is a section header (starts with newline + ===)
        is_section = (
            record.msg.startswith("\n=== ") if isinstance(record.msg, str) else False
        )

        # Check if this is an error message
        is_error = record.levelno >= logging.ERROR

        if is_section:
            # Full timestamp format for sections and errors
            if is_error:
                # Red timestamp and level for errors
                fmt = f"{Fore.RED}%(asctime)s{Style.RESET_ALL}"
                fmt += f" [{Fore.RED}ERROR{Style.RESET_ALL}] %(message)s"
                self._style._fmt = fmt
            else:
                # Cyan timestamp and yellow level for sections
                fmt = f"\n{Fore.CYAN}%(asctime)s{Style.RESET_ALL}"
                fmt += f" [{Fore.YELLOW}INFO{Style.RESET_ALL}] %(message)s"
                self._style._fmt = fmt
            self.datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            # No timestamp or level for other logs
            self._style._fmt = "%(message)s"

        # Format the message first
        formatted_msg = super().format(record)

        # If this is a section header, color the header text but keep equals signs black
        if is_section:
            # Split the header into parts (handle the newline)
            parts = formatted_msg.split("===")
            if len(parts) == 3:  # Should be ["\n", " HEADER ", ""]
                # Color the middle part (the header text) while keeping === black
                color = (
                    Fore.RED if is_error else Fore.MAGENTA
                )  # Red for errors, purple for info
                formatted_msg = (
                    parts[0] + "===" + color + parts[1] + Style.RESET_ALL + "==="
                )

        return formatted_msg


def set_error_post_hook(
    hook: Callable[
        [
            Exception,
            str,
            str,
            Optional[str],
            Optional[str],
            Optional[str],
            Optional[str],
        ],
        None,
    ],
):
    """Register an external hook to post errors to a server."""
    global _external_error_logging_hook
    _external_error_logging_hook = hook


def set_logs_post_hook(
    hook: Callable[
        [str, str, Optional[str], Optional[str], Optional[str], Optional[str]], None
    ],
):
    """Register an external hook to post logs to a server."""
    global _external_logging_hook
    _external_logging_hook = hook


def set_conversation_context(context: Dict[str, Any]) -> None:
    """Set the conversation context that will be passed to the conversation hook.

    Args:
        context: Dictionary of context data to pass to the conversation hook.
               This can include any additional fields needed by the hook.
    """
    current = conversation_context_var.get()
    conversation_context_var.set({**current, **context})


def set_conversation_hook(
    hook: Callable[[str, str, Any, str, Dict[str, Any], str], None],
):
    """Register an external hook to record conversations.

    Args:
        hook: Function that takes (conversation_id, role, content, model, context)
             where context contains additional data to include in the log
    """
    global _conversation_hook
    _conversation_hook = hook


def _post_log(level: str, message: str):
    if _external_logging_hook:
        try:
            _external_logging_hook(
                logLevel=level,
                message=message,
                task_id=task_id_var.get(),
                swarm_bounty_id=swarm_bounty_id_var.get(),
                signature=signature_var.get(),
                todo_uuid=todo_uuid_var.get(),
            )
        except Exception as post_error:
            logger.warning(f"Failed to send log to external hook: {post_error}")


def configure_logging():
    """Configure logging for the application."""
    global _logging_configured
    if _logging_configured:
        return

    try:
        # Remove any existing handlers to prevent duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = SectionFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        logger.info("Logging configured: INFO+ to console")
        _logging_configured = True

    except Exception as e:
        # If logging setup fails, ensure basic console logging is available
        print(f"Failed to configure logging: {e}", file=sys.stderr)


def format_value(value: Any) -> str:
    """Format a value for logging, handling multiline strings."""
    if isinstance(value, str) and "\n" in value:
        # Indent multiline strings
        return "\n    " + value.replace("\n", "\n    ")
    return str(value)


def log_section(name: str, logToServer: bool = True) -> None:
    """Log a section header with consistent formatting."""
    if not _logging_configured:
        configure_logging()
    msg = f"\n=== {name.upper()} ==="
    logger.info(msg)
    # if logToServer:
    #     _post_log("INFO", msg)


def log_key_value(key: str, value: Any, logToServer: bool = True) -> None:
    """Log a key-value pair with consistent formatting."""
    if not _logging_configured:
        configure_logging()
    msg = f"{key}: {format_value(value)}"
    logger.info(msg)
    # if logToServer:
    #     _post_log("INFO", msg)


def log_value(value: str, logToServer: bool = True) -> None:
    """Log a value with consistent formatting."""
    if not _logging_configured:
        configure_logging()
    msg = format_value(value)
    logger.info(msg)
    # if logToServer:
    #     _post_log("INFO", msg)


def log_dict(data: dict, prefix: str = "") -> None:
    """Log a dictionary with consistent formatting."""
    for key, value in data.items():
        if isinstance(value, dict):
            log_dict(value, f"{prefix}{key}.")
        else:
            log_key_value(f"{prefix}{key}", value)


def log_tool_call(tool_name: str, inputs: dict) -> None:
    """Log a tool call with consistent formatting."""
    if not _logging_configured:
        configure_logging()
    log_section(f"EXECUTING TOOL: {tool_name}")
    if inputs:
        logger.info("INPUTS:")
        log_dict(inputs)


def log_tool_result(result: Any) -> None:
    """Log a tool result with consistent formatting."""
    if not _logging_configured:
        configure_logging()
    logger.info("RESULT:")
    if isinstance(result, dict):
        # Handle success/failure responses
        if "success" in result:
            if result["success"]:
                logger.info("✓ Success")
                # For successful operations, show the main result or message
                if "message" in result:
                    logger.info(format_value(result["message"]))
                # Show other relevant fields (excluding success flag and error)
                for key, value in result.items():
                    if key not in ["success", "error", "message"]:
                        log_key_value(key, value)
            else:
                logger.info("✗ Failed")
                if "error" in result:
                    logger.info(format_value(result["error"]))
        else:
            # For other responses, just show key-value pairs
            log_dict(result)
    else:
        logger.info(format_value(result))


def log_error(
    error: Exception,
    context: str = "",
    include_traceback: bool = True,
    logToServer: bool = True,
) -> None:
    """Log an error with consistent formatting and optional stack trace."""
    if not _logging_configured:
        configure_logging()
    logger.error(f"\n=== {context.upper() if context else 'ERROR'} ===")
    logger.info(f"Error: {str(error)}")
    if include_traceback and error.__traceback__:
        logger.info("Stack trace:")
        for line in traceback.format_tb(error.__traceback__):
            logger.info(line.rstrip())
    # External posting if configured
    if _external_error_logging_hook and logToServer:
        stack_trace = ""
        if include_traceback and error.__traceback__:
            stack_trace = "".join(traceback.format_tb(error.__traceback__))
        try:
            _external_error_logging_hook(
                error,
                context or "ERROR",
                stack_trace,
                task_id=task_id_var.get(),
                swarm_bounty_id=swarm_bounty_id_var.get(),
                signature=signature_var.get(),
                todo_uuid=todo_uuid_var.get(),
            )
        except Exception as post_error:
            logger.warning(f"Failed to send error to external hook: {post_error}")


def log_execution_time(func):
    """Decorator to log function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _logging_configured:
            configure_logging()
        import time

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds")
            raise

    return wrapper


def add_file_logging(log_file: str) -> None:
    """Add file logging with rotation."""
    if not _logging_configured:
        configure_logging()
    try:
        from logging.handlers import RotatingFileHandler

        # Create log directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.info(f"File logging enabled: {log_file}")
    except Exception as e:
        logger.error(f"Failed to set up file logging: {e}")


def log_tool_response(response_str: str, tool_use_id: str = None) -> None:
    """Log a tool response with consistent formatting.

    Args:
        response_str: The tool response string
        tool_use_id: Optional tool use ID
    """
    if not _logging_configured:
        configure_logging()
    if tool_use_id:
        logger.info(f"TOOL USE ID: {tool_use_id}")
    logger.info("RESPONSE:")
    try:
        # Try to parse as Python dict string
        response = ast.literal_eval(response_str)
        if isinstance(response, dict):
            # Handle success/failure responses
            if "success" in response:
                if response["success"]:
                    logger.info("✓ Success")
                    # For successful operations, show the main result or message
                    if "message" in response:
                        logger.info(format_value(response["message"]))
                    # Show other relevant fields (excluding success flag and error)
                    for key, value in response.items():
                        if key not in ["success", "error", "message"]:
                            log_key_value(key, value)
                else:
                    logger.info("✗ Failed")
                    if "error" in response:
                        logger.info(format_value(response["error"]))
            else:
                # For other responses, just show key-value pairs
                log_dict(response)
        else:
            logger.info(format_value(response_str))
    except (ValueError, SyntaxError):
        # If not a valid Python literal, log as formatted string
        logger.info(format_value(response_str))


def record_conversation(conversation_id: str, role: str, content: Any, model: str):
    """Record a conversation message using the registered hook if available.

    Args:
        conversation_id: Unique identifier for the conversation
        role: Role of the message sender (e.g. "user", "assistant")
        content: Content of the message
        model: Model used for the conversation
    """
    if _conversation_hook:
        try:
            context = conversation_context_var.get()
            _conversation_hook(
                conversation_id, role, content, model, context, todo_uuid_var.get()
            )
        except Exception as e:
            logger.warning(f"Failed to record conversation: {e}")
