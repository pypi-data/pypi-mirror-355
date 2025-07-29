# bedrock-server-manager/bedrock_server_manager/web/routes/backup_restore_routes.py
"""
Flask Blueprint handling web routes and API endpoints for server backup
and restore operations.
"""

import os
import logging
from typing import Dict, Any, Tuple

# Third-party imports
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
)

# Local imports
from bedrock_server_manager.api import backup_restore as backup_restore_api
from bedrock_server_manager.config.settings import (
    settings,
    app_name,
)
from bedrock_server_manager.utils.general import get_base_dir
from bedrock_server_manager.web.utils.auth_decorators import (
    auth_required,
    get_current_identity,
)
from bedrock_server_manager.web.routes.auth_routes import login_required, csrf
from bedrock_server_manager.error import (
    MissingArgumentError,
    FileNotFoundError,
    InvalidInputError,
    TypeError,
    FileOperationError,
)

# Initialize logger
logger = logging.getLogger("bedrock_server_manager")

# Create Blueprint
backup_restore_bp = Blueprint(
    "backup_restore_routes",
    __name__,
    template_folder="../templates",
    static_folder="../static",
)


# --- Route: Backup Menu Page ---
@backup_restore_bp.route("/server/<string:server_name>/backup", methods=["GET"])
@login_required  # Requires web session
def backup_menu_route(server_name: str) -> Response:
    """
    Renders the main backup menu page for a specific server.

    Args:
        server_name: The name of the server passed in the URL.

    Returns:
        Rendered HTML page ('backup_menu.html').
    """
    identity = get_current_identity()  # For logging
    logger.info(f"User '{identity}' accessed backup menu for server '{server_name}'.")
    # Note: Server existence validation happens globally via before_request handler
    return render_template(
        "backup_menu.html", server_name=server_name, app_name=app_name
    )


@backup_restore_bp.route(
    "/api/server/<string:server_name>/backups/list/<string:backup_type>",
    methods=["GET"],
)
@csrf.exempt
@auth_required
def list_server_backups_route(
    server_name: str, backup_type: str
) -> Tuple[Response, int]:
    """
    API endpoint to list available backup files (basenames only) for a specific server and type.

    Args:
        server_name (str): The name of the server, passed in the URL path.
        backup_type (str): The type of backups to list ("world" or "config"),
                           passed in the URL path.

    Returns:
        JSON response containing the list of backup file basenames or an error message.
        - 200 OK: {"status": "success", "backups": List[str]} (basenames)
        - 400 Bad Request: {"status": "error", "message": "Error description..."}
        - 500 Internal Server Error: {"status": "error", "message": "..."}
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: Request to list '{backup_type}' backups for server '{server_name}' by user '{identity}'."
    )

    status_code = 500
    result_dict: Dict[str, Any]

    try:
        api_result = (
            backup_restore_api.list_backup_files(  # Call API module, gets full paths
                server_name=server_name, backup_type=backup_type
            )
        )

        if api_result.get("status") == "success":
            status_code = 200
            full_paths = api_result.get("backups", [])
            basenames = [os.path.basename(p) for p in full_paths]
            result_dict = {  # Reconstruct the result_dict for jsonify
                "status": "success",
                "backups": basenames,  # Use basenames here
            }
            logger.info(
                f"API List Backups: Successfully listed {len(basenames)} backup basenames for '{server_name}' ({backup_type})."
            )
        else:
            status_code = 500
            result_dict = api_result  # Pass through the error dictionary
            logger.warning(
                f"API List Backups: Handler for '{server_name}' ({backup_type}) returned error: {result_dict.get('message')}"
            )

    except (MissingArgumentError, InvalidInputError) as e:
        logger.warning(
            f"API List Backups: Client input error for '{server_name}' ({backup_type}): {e}"
        )
        result_dict = {"status": "error", "message": str(e)}
        status_code = 400
    except FileOperationError as e:
        logger.error(
            f"API List Backups: Configuration/File operation error for '{server_name}' ({backup_type}): {e}",
            exc_info=True,
        )
        result_dict = {"status": "error", "message": f"Configuration error: {e}"}
        status_code = 500
    except Exception as e:
        logger.error(
            f"API List Backups: Unexpected critical error in route for '{server_name}' ({backup_type}): {e}",
            exc_info=True,
        )
        result_dict = {
            "status": "error",
            "message": "A critical unexpected server error occurred while listing backups.",
        }
        status_code = 500

    return jsonify(result_dict), status_code


# --- Route: Backup Config Selection Page ---
@backup_restore_bp.route("/server/<string:server_name>/backup/config", methods=["GET"])
@login_required  # Requires web session
def backup_config_select_route(server_name: str) -> Response:
    """
    Renders the page for selecting specific configuration files to back up.

    Args:
        server_name: The name of the server passed in the URL.

    Returns:
        Rendered HTML page ('backup_config_options.html').
    """
    identity = get_current_identity()  # For logging
    logger.info(
        f"User '{identity}' accessed config backup selection page for server '{server_name}'."
    )
    return render_template(
        "backup_config_options.html", server_name=server_name, app_name=app_name
    )


# --- API Route: Backup Action ---
@backup_restore_bp.route(
    "/api/server/<string:server_name>/backup/action", methods=["POST"]
)
@csrf.exempt  # Exempt API endpoint from CSRF (uses JWT or session implicitly checked by auth_required)
@auth_required  # Requires session OR JWT
def backup_action_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to trigger a server backup operation.

    Expects a JSON body specifying the type of backup.
    JSON Body Example:
        {"backup_type": "world"}
        {"backup_type": "config", "file_to_backup": "server.properties"}
        {"backup_type": "all"}

    Args:
        server_name: The name of the server passed in the URL.

    Returns:
        JSON response indicating success or failure, with appropriate HTTP status code.
        - 200 OK on success: {"status": "success", "message": "..."}
        - 400 Bad Request on invalid input.
        - 500 Internal Server Error on backup failure.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: Backup action requested for server '{server_name}' by user '{identity}'."
    )

    # --- Input Validation ---
    data = request.get_json(
        silent=True
    )  # Use silent=True to avoid 400 on non-JSON, handle manually
    if not data or not isinstance(data, dict):
        logger.warning(f"API Backup '{server_name}': Invalid/missing JSON body.")
        return (
            jsonify(status="error", message="Invalid or missing JSON request body."),
            400,
        )

    logger.debug(f"API Backup '{server_name}': Received data: {data}")
    backup_type = data.get("backup_type", "").lower()  # Normalize type
    file_to_backup = data.get("file_to_backup")

    valid_types = ["world", "config", "all"]
    if backup_type not in valid_types:
        msg = f"Missing or invalid 'backup_type'. Must be one of: {valid_types}."
        logger.warning(f"API Backup '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 400

    if backup_type == "config":
        if not file_to_backup or not isinstance(file_to_backup, str):
            msg = "Missing or invalid 'file_to_backup' (string) required for config backup type."
            logger.warning(f"API Backup '{server_name}': {msg}")
            return jsonify(status="error", message=msg), 400
        # Strip whitespace from relative filename
        file_to_backup = file_to_backup.strip()

    # --- Call API Handler ---
    result: Dict[str, Any] = {}
    status_code = 500  # Default to internal error
    try:
        base_dir = get_base_dir()  # May raise FileOperationError

        if backup_type == "world":
            logger.debug(
                f"Calling API handler: backup_restore_api.backup_world for '{server_name}'"
            )
            result = backup_restore_api.backup_world(server_name, base_dir)
        elif backup_type == "config":
            logger.debug(
                f"Calling API handler: backup_restore_api.backup_config_file for '{server_name}', file '{file_to_backup}'"
            )
            result = backup_restore_api.backup_config_file(
                server_name, file_to_backup, base_dir
            )
        elif backup_type == "all":
            logger.debug(
                f"Calling API handler: backup_restore_api.backup_all for '{server_name}'"
            )
            result = backup_restore_api.backup_all(server_name, base_dir)

        logger.debug(f"API Backup '{server_name}': Handler response: {result}")

        # Determine status code based on handler result
        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            logger.info(
                f"API Backup '{server_name}' (type: {backup_type}) completed successfully."
            )
        else:
            # Handler indicated failure or returned unexpected format
            status_code = (
                500  # Treat handler errors as internal server errors for API response
            )
            error_msg = (
                result.get("message", "Unknown error during backup operation.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(
                f"API Backup '{server_name}' (type: {backup_type}) failed: {error_msg}"
            )
            # Ensure error structure in response
            result = {"status": "error", "message": error_msg}

    except (MissingArgumentError, FileNotFoundError, TypeError, InvalidInputError) as e:
        # Catch specific input/validation errors potentially raised by API handlers
        logger.warning(f"API Backup '{server_name}': Input error: {e}", exc_info=True)
        status_code = 400
        result = {"status": "error", "message": f"Invalid input or file not found: {e}"}
    except FileOperationError as e:  # Catch base_dir config errors
        logger.error(
            f"API Backup '{server_name}': Configuration error: {e}", exc_info=True
        )
        status_code = 500
        result = {"status": "error", "message": f"Server configuration error: {e}"}
    except Exception as e:
        # Catch unexpected errors during API orchestration
        logger.error(
            f"API Backup '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {"status": "error", "message": f"An unexpected error occurred: {e}"}

    return jsonify(result), status_code


# --- Route: Restore Menu Page ---
@backup_restore_bp.route("/server/<string:server_name>/restore", methods=["GET"])
@login_required  # Requires web session
def restore_menu_route(server_name: str) -> Response:
    """
    Renders the main restore menu page for a specific server.

    Args:
        server_name: The name of the server passed in the URL.

    Returns:
        Rendered HTML page ('restore_menu.html').
    """
    identity = get_current_identity()  # For logging
    logger.info(f"User '{identity}' accessed restore menu for server '{server_name}'.")
    return render_template(
        "restore_menu.html", server_name=server_name, app_name=app_name
    )


# --- API Route: Restore Action ---
@backup_restore_bp.route(
    "/api/server/<string:server_name>/restore/action", methods=["POST"]
)
@csrf.exempt  # API endpoint
@auth_required  # Requires session OR JWT
def restore_action_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to trigger a server restoration from a specified backup file.

    Expects JSON body with 'backup_file' key containing the path to the backup file
    (relative to the configured BACKUP_DIR) and 'restore_type'.
    Performs validation to ensure the backup file path is within the configured BACKUP_DIR.

    Args:
        server_name: The name of the server passed in the URL.

    JSON Request Body Example:
        {"restore_type": "world", "backup_file": "MyServerName/world_backup_xyz.mcworld"}
        (Where "world_backup_xyz.mcworld" is relative to BACKUP_DIR)

    Returns:
        JSON response indicating success or failure, with appropriate HTTP status code.
        - 200 OK on success: {"status": "success", "message": "..."}
        - 400 Bad Request on invalid input or invalid backup file path.
        - 404 Not Found if backup file doesn't exist.
        - 500 Internal Server Error on restore failure or config issues.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: Restore action requested for server '{server_name}' by user '{identity}'."
    )

    # --- Input Validation (Initial JSON structure) ---
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        logger.warning(f"API Restore '{server_name}': Invalid/missing JSON body.")
        return (
            jsonify(status="error", message="Invalid or missing JSON request body."),
            400,
        )

    logger.debug(f"API Restore '{server_name}': Received data: {data}")
    restore_type = data.get("restore_type", "").lower()
    # Expecting *relative* path from client selection
    relative_backup_file_path = data.get("backup_file")

    valid_types = ["world", "config"]
    if restore_type not in valid_types:
        msg = f"Missing or invalid 'restore_type'. Must be one of: {valid_types}."
        logger.warning(f"API Restore '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 400

    if not relative_backup_file_path or not isinstance(relative_backup_file_path, str):
        msg = "Missing or invalid 'backup_file' in request. Expected relative path to backup file."
        logger.warning(f"API Restore '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 400

    # --- Path Construction and Validation ---
    result: Dict[str, Any] = {}
    status_code = 500
    try:
        backup_base_dir = settings.get("BACKUP_DIR")
        if not backup_base_dir:
            # This will be caught by the FileOperationError handler below
            raise FileOperationError(
                "BACKUP_DIR setting is missing or empty in configuration."
            )

        # Construct the full path from the base backup directory and the relative path
        full_backup_file_path = os.path.normpath(
            os.path.join(backup_base_dir, server_name, relative_backup_file_path)
        )

        logger.debug(
            f"API Restore '{server_name}': Validating backup file. "
            f"Relative: '{relative_backup_file_path}', "
            f"Full: '{full_backup_file_path}', "
            f"Allowed Base: '{backup_base_dir}'"
        )

        # Security Check: Ensure the requested file is within the allowed backup directory
        # os.path.abspath is used to resolve any '..' and ensure a true comparison
        if not os.path.abspath(full_backup_file_path).startswith(
            os.path.abspath(backup_base_dir)
        ):
            msg = "Invalid backup file path: Path is outside the allowed backup directory."
            logger.error(
                f"API Restore '{server_name}': Security violation - {msg} "
                f"Attempted relative path: '{relative_backup_file_path}', "
                f"Resolved full path: '{full_backup_file_path}'"
            )
            return jsonify(status="error", message=msg), 400  # Bad Request

        # Check if file exists
        if not os.path.isfile(full_backup_file_path):
            msg = (
                f"Backup file not found at specified path: {full_backup_file_path} "
                f"(from relative: {relative_backup_file_path})"
            )
            logger.warning(f"API Restore '{server_name}': {msg}")
            return (
                jsonify(status="error", message="Backup file not found."),
                404,
            )  # Not Found

        logger.debug(
            f"API Restore '{server_name}': Backup file path validation successful for '{full_backup_file_path}'."
        )

        # --- Call API Handler ---
        base_dir = get_base_dir()  # Base dir for server installations

        if restore_type == "world":
            logger.debug(
                f"Calling API handler: backup_restore_api.restore_world for '{server_name}', file '{full_backup_file_path}'"
            )
            result = backup_restore_api.restore_world(
                server_name, full_backup_file_path, base_dir
            )
        elif restore_type == "config":
            logger.debug(
                f"Calling API handler: backup_restore_api.restore_config_file for '{server_name}', file '{full_backup_file_path}'"
            )
            result = backup_restore_api.restore_config_file(
                server_name, full_backup_file_path, base_dir
            )
        else:
            # This case should have been caught earlier by valid_types check,
            # but as a safeguard:
            msg = f"Internal error: Unknown restore_type '{restore_type}' made it past validation."
            logger.error(f"API Restore '{server_name}': {msg}")
            return jsonify(status="error", message=msg), 500

        logger.debug(f"API Restore '{server_name}': Handler response: {result}")

        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            # Use basename of the relative path for a user-friendly filename in the message
            success_msg = (
                f"Restoration from '{os.path.basename(relative_backup_file_path)}' "
                f"(type: {restore_type}) completed successfully."
            )
            logger.info(f"API Restore '{server_name}': {success_msg}")
            result["message"] = success_msg  # Ensure message is set/updated
        else:
            status_code = 500  # Treat handler errors as internal server errors
            error_msg = (
                result.get("message", "Unknown error during restore operation.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(
                f"API Restore '{server_name}' (type: {restore_type}) failed: {error_msg}"
            )
            # Ensure result has status and message for consistent error response
            result = {"status": "error", "message": error_msg}

    except FileNotFoundError as e:
        # This might be caught if the file disappears between os.path.isfile and actual use,
        # or if an internal operation within the API handler raises it.
        logger.warning(
            f"API Restore '{server_name}': File not found during operation: {e}",
            exc_info=True,
        )
        status_code = 404
        result = {"status": "error", "message": f"Backup file not found: {e}"}
    except (MissingArgumentError, TypeError, InvalidInputError) as e:
        logger.warning(f"API Restore '{server_name}': Input error: {e}", exc_info=True)
        status_code = 400
        result = {"status": "error", "message": f"Invalid input or configuration: {e}"}
    except (
        FileOperationError
    ) as e:  # Catches BACKUP_DIR issues or other file ops errors
        logger.error(
            f"API Restore '{server_name}': Configuration/File error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"Server configuration or file error: {e}",
        }
    except Exception as e:
        logger.error(
            f"API Restore '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"An unexpected error occurred during restore: {e}",
        }

    return jsonify(result), status_code


# --- Route: Select Backup for Restore Page ---
@backup_restore_bp.route(
    "/server/<string:server_name>/restore/select", methods=["POST"]
)
@login_required  # Requires web session
def restore_select_backup_route(server_name: str) -> Response:
    """
    Handles the form submission from the restore menu. Lists available backups
    of the selected type for the user to choose from.

    Args:
        server_name: The name of the server passed in the URL.

    Form Data Expected:
        restore_type: "world" or "config"

    Returns:
        Renders 'restore_select_backup.html' with the list of backups on success.
        Redirects back to the restore menu with a flash message on error.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"User '{identity}' submitted restore type selection for server '{server_name}'."
    )

    # Get restore type from form data
    restore_type = request.form.get("restore_type", "").lower()
    logger.debug(f"Restore type selected from form: '{restore_type}'")

    # Validate restore type
    valid_types = ["world", "config"]
    if restore_type not in valid_types:
        error_msg = f"Invalid restore type selected: '{restore_type}'. Please go back and select 'world' or 'config'."
        logger.warning(f"Restore selection for '{server_name}': {error_msg}")
        flash(error_msg, "warning")
        return redirect(
            url_for(".restore_menu_route", server_name=server_name)
        )  # Use relative endpoint '.'

    # Call the API function to list backups
    logger.info(
        f"Listing backups of type '{restore_type}' for server '{server_name}'..."
    )
    try:
        # API func handles base_dir resolution and BACKUP_DIR check
        list_response = backup_restore_api.list_backup_files(server_name, restore_type)
        logger.debug(f"List backups response: {list_response}")

        if list_response.get("status") == "success":
            backups_list = list_response.get("backups", [])
            if not backups_list:
                flash(
                    f"No '{restore_type}' backups found for server '{server_name}'.",
                    "info",
                )
                return redirect(url_for(".restore_menu_route", server_name=server_name))

            logger.debug(
                f"Rendering restore selection page with {len(backups_list)} backups."
            )
            # Render selection page, passing full paths and basenames
            backup_details = [
                {"path": p, "name": os.path.basename(p)} for p in backups_list
            ]
            return render_template(
                "restore_select_backup.html",
                server_name=server_name,
                restore_type=restore_type,
                backups=backup_details,  # Pass list of dicts with path and name
                app_name=app_name,
            )
        else:
            # Error reported by the list_backup_files handler
            error_msg = f"Error listing backups: {list_response.get('message', 'Unknown error')}"
            logger.error(
                f"Error listing backups for '{server_name}' ({restore_type}): {error_msg}"
            )
            flash(error_msg, "error")
            return redirect(url_for(".restore_menu_route", server_name=server_name))

    except (
        MissingArgumentError,
        FileOperationError,
    ) as e:  # Catch errors raised directly by list_backup_files
        logger.error(
            f"Error calling list_backup_files for '{server_name}': {e}", exc_info=True
        )
        flash(f"Error listing backups: {e}", "error")
        return redirect(url_for(".restore_menu_route", server_name=server_name))
    except Exception as e:
        logger.error(
            f"Unexpected error listing backups for '{server_name}': {e}", exc_info=True
        )
        flash("An unexpected error occurred while listing backups.", "error")
        return redirect(url_for(".restore_menu_route", server_name=server_name))


# --- API Route: Restore All ---
@backup_restore_bp.route(
    "/api/server/<string:server_name>/restore/all", methods=["POST"]
)
@csrf.exempt  # API endpoint
@auth_required  # Requires session OR JWT
def restore_all_api_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to trigger restoring all files (world and configs) from the latest backups.

    Args:
        server_name: The name of the server passed in the URL.

    Returns:
        JSON response indicating success or failure, with appropriate HTTP status code.
        - 200 OK on success: {"status": "success", "message": "..."}
        - 500 Internal Server Error on restore failure.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: Restore All action requested for server '{server_name}' by user '{identity}'."
    )

    result: Dict[str, Any] = {}
    status_code = 500
    try:
        base_dir = get_base_dir()  # May raise FileOperationError

        # Call the restore_all API handler directly
        logger.debug(
            f"Calling API handler: backup_restore_api.restore_all for '{server_name}'"
        )
        result = backup_restore_api.restore_all(
            server_name, base_dir
        )  # API func returns dict
        logger.debug(f"API Restore All '{server_name}': Handler response: {result}")

        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            success_msg = f"Restore All operation for server '{server_name}' completed successfully."
            logger.info(f"API: {success_msg}")
            # Ensure message key exists for consistency
            result["message"] = result.get("message", success_msg)
        else:
            status_code = 500
            error_msg = (
                result.get("message", "Unknown error during restore all operation.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(f"API Restore All '{server_name}' failed: {error_msg}")
            result = {"status": "error", "message": error_msg}  # Ensure error status

    except (
        MissingArgumentError,
        FileOperationError,
    ) as e:  # Catch errors raised by API handler setup
        logger.error(
            f"API Restore All '{server_name}': Input or Configuration error: {e}",
            exc_info=True,
        )
        status_code = 500  # Treat config errors as internal server error
        result = {"status": "error", "message": f"Configuration or input error: {e}"}
    except Exception as e:
        logger.error(
            f"API Restore All '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"An unexpected error occurred during restore all: {e}",
        }

    return jsonify(result), status_code
