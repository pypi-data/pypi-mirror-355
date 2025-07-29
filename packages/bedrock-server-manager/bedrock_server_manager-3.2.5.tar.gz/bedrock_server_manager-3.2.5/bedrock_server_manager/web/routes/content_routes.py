# bedrock-server-manager/bedrock_server_manager/web/routes/content_routes.py
"""
Flask Blueprint for handling web routes and API endpoints related to
server content management (Worlds, Addons).
"""

import os
import logging
from typing import Tuple, Dict, Any, List

# Third-party imports
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    jsonify,
    Response,
)

# Local imports
from bedrock_server_manager.api import world as world_api
from bedrock_server_manager.api import addon as addon_api
from bedrock_server_manager.api import utils as utils_api
from bedrock_server_manager.utils.general import get_base_dir
from bedrock_server_manager.config.settings import settings, app_name
from bedrock_server_manager.web.routes.auth_routes import login_required, csrf
from bedrock_server_manager.web.utils.auth_decorators import (
    auth_required,
    get_current_identity,
)
from bedrock_server_manager.error import (
    FileOperationError,
    DownloadExtractError,
    DirectoryError,
    MissingArgumentError,
    InvalidServerNameError,
    InvalidInputError,
    AddonExtractError,
    InvalidAddonPackTypeError,
    BackupWorldError,
)

logger = logging.getLogger("bedrock_server_manager")

# Blueprint for content management routes
content_bp = Blueprint(
    "content_routes",
    __name__,
    template_folder="../templates",
    static_folder="../static",
)


# -- List content files --


@content_bp.route("/api/content/worlds", methods=["GET"])
@csrf.exempt
@auth_required
def list_worlds_route() -> Tuple[Response, int]:
    """
    API endpoint to list available world content files (basenames only).
    Looks in CONTENT_DIR/worlds for .mcworld files.

    Returns:
        JSON response with list of world file basenames or an error.
        - 200 OK: {"status": "success", "files": List[str]} (basenames)
        - 500 Internal Server Error: {"status": "error", "message": "..."}
    """
    logger.info("API Route: Request to list world content files.")
    status_code = 500
    response_dict: Dict[str, Any]

    try:
        api_result = utils_api.list_world_content_files()

        if api_result.get("status") == "success":
            status_code = 200
            full_paths = api_result.get("files", [])
            basenames = [os.path.basename(p) for p in full_paths]
            response_dict = {
                "status": "success",
                "files": basenames,
                "message": api_result.get(
                    "message"
                ),  # Pass through message like "No matching files found"
            }
            # Remove message if files were found and message was only for no files
            if basenames and response_dict.get("message") == "No matching files found.":
                response_dict.pop("message")

            logger.info(f"API Route: Listed {len(basenames)} world file basenames.")
        else:  # Error from API layer
            response_dict = api_result
            # Determine status code based on error (e.g., CONTENT_DIR missing vs. dir not found)
            if "CONTENT_DIR setting is missing" in response_dict.get("message", ""):
                status_code = 500  # Configuration error
            elif "Content directory not found" in response_dict.get("message", ""):
                # This case is handled by list_content_files returning an error,
                # if worlds_dir doesn't exist.
                status_code = 404  # Or 500 if considered a server setup issue
            else:
                status_code = 500  # Generic server error
            logger.warning(
                f"API Route: Error listing worlds: {response_dict.get('message')}"
            )

    except Exception as e:  # Catch truly unexpected errors in the route itself
        logger.error(
            f"API Route: Unexpected critical error listing worlds: {e}", exc_info=True
        )
        response_dict = {
            "status": "error",
            "message": "A critical server error occurred.",
        }
        status_code = 500

    return jsonify(response_dict), status_code


@content_bp.route("/api/content/addons", methods=["GET"])
@csrf.exempt
@auth_required
def list_addons_route() -> Tuple[Response, int]:
    """
    API endpoint to list available addon content files (basenames only).
    Looks in CONTENT_DIR/addons for .mcpack, .mcaddon.

    Returns:
        JSON response with list of addon file basenames or an error.
        - 200 OK: {"status": "success", "files": List[str]} (basenames)
        - 500 Internal Server Error: {"status": "error", "message": "..."}
    """
    logger.info("API Route: Request to list addon content files.")
    status_code = 500
    response_dict: Dict[str, Any]

    try:
        api_result = utils_api.list_addon_content_files()

        if api_result.get("status") == "success":
            status_code = 200
            full_paths = api_result.get("files", [])
            basenames = [os.path.basename(p) for p in full_paths]
            response_dict = {
                "status": "success",
                "files": basenames,
                "message": api_result.get("message"),
            }
            if basenames and response_dict.get("message") == "No matching files found.":
                response_dict.pop("message")
            logger.info(f"API Route: Listed {len(basenames)} addon file basenames.")
        else:  # Error from API layer
            response_dict = api_result
            if "CONTENT_DIR setting is missing" in response_dict.get("message", ""):
                status_code = 500
            elif "Content directory not found" in response_dict.get("message", ""):
                status_code = 404  # Or 500
            else:
                status_code = 500
            logger.warning(
                f"API Route: Error listing addons: {response_dict.get('message')}"
            )

    except Exception as e:
        logger.error(
            f"API Route: Unexpected critical error listing addons: {e}", exc_info=True
        )
        response_dict = {
            "status": "error",
            "message": "A critical server error occurred.",
        }
        status_code = 500

    return jsonify(response_dict), status_code


# --- Route: Install World Selection Page ---
@content_bp.route("/server/<string:server_name>/install_world")
@login_required  # Requires web session
def install_world_route(server_name: str) -> Response:
    """
    Renders the page allowing users to select a world (.mcworld file) for installation.

    Lists available .mcworld files from the content/worlds directory.

    Args:
        server_name: The name of the server to install the world to (from URL path).

    Returns:
        Rendered HTML page 'select_world.html' with a list of available world files.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"User '{identity}' accessed world install selection page for server '{server_name}'."
    )

    content_dir = os.path.join(settings.get("CONTENT_DIR"), "worlds")
    logger.debug(f"World content directory: {content_dir}")

    # API call to list available .mcworld files
    list_result: Dict[str, Any] = utils_api.list_content_files(content_dir, ["mcworld"])
    logger.debug(f"List content files API result: {list_result}")

    world_files: List[str] = []
    if list_result.get("status") == "error":
        error_msg = (
            f"Error listing world files: {list_result.get('message', 'Unknown error')}"
        )
        flash(error_msg, "error")
        logger.error(
            f"Error listing world files for server '{server_name}': {error_msg}"
        )
    else:
        world_files = list_result.get("files", [])  # Safely get files list

    logger.debug(
        f"Rendering 'select_world.html' template for server '{server_name}' with {len(world_files)} files."
    )
    return render_template(
        "select_world.html",
        server_name=server_name,
        world_files=world_files,  # List of full paths to .mcworld files
        app_name=app_name,
    )


# --- API Route: Install World ---
@content_bp.route("/api/server/<string:server_name>/world/install", methods=["POST"])
@csrf.exempt  # Exempt API endpoint from CSRF protection (using JWT or session auth)
@auth_required  # Requires session OR JWT authentication
def install_world_api_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to install a user-selected world (.mcworld file) to a server.

    Expects JSON body with 'filename' key containing the path to the .mcworld file
    (relative to the 'content/worlds' directory).

    Args:
        server_name: The name of the server to install the world to (from URL path).

    JSON Request Body Example:
        {"filename": "/path/relative/to/content/worlds/MyWorld.mcworld"}

    Returns:
        JSON response indicating success or failure of the world installation:
        - 200 OK: {"status": "success", "message": "World '...' installed successfully for server '...'."}
        - 400 Bad Request: Invalid JSON, missing filename.
        - 500 Internal Server Error: World import process failed.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: World install requested for server '{server_name}' by user '{identity}'."
    )

    # --- Input Validation ---
    data = request.get_json(
        silent=True
    )  # Use silent=True to avoid automatic 400 on bad JSON
    if not data or not isinstance(data, dict):
        logger.warning(
            f"API Install World '{server_name}': Invalid/missing JSON request body."
        )
        return (
            jsonify(status="error", message="Invalid or missing JSON request body."),
            400,
        )

    selected_file_path = data.get(
        "filename"
    )  # Expecting *relative* path from selection page

    if not selected_file_path or not isinstance(selected_file_path, str):
        msg = "Missing or invalid 'filename' in request body. Expected relative path to .mcworld file."
        logger.warning(f"API Install World '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 400

    content_base_dir = os.path.join(
        settings.get("CONTENT_DIR"), "worlds"
    )  # Base dir for worlds
    full_world_file_path = os.path.normpath(
        os.path.join(content_base_dir, selected_file_path)
    )  # Resolve relative path
    logger.debug(
        f"API Install World '{server_name}': Attempting to install from file: {full_world_file_path}"
    )

    # Security: Ensure path is still within the allowed content directory after joining and normalization
    if not os.path.abspath(full_world_file_path).startswith(
        os.path.abspath(content_base_dir)
    ):
        msg = "Invalid filename: Filename must be within the allowed content directory."
        logger.warning(
            f"API Install World '{server_name}': {msg} Attempted path: {full_world_file_path}"
        )
        return jsonify(status="error", message=msg), 400
    if not os.path.isfile(full_world_file_path):
        msg = f"Selected world file not found: {full_world_file_path}"
        logger.warning(f"API Install World '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 404

    # --- Call API Handler ---
    result: Dict[str, Any] = {}
    status_code = 500  # Default to internal server error
    try:
        base_dir = get_base_dir()  # May raise FileOperationError

        # Call the core world import API function
        logger.debug(
            f"Calling API handler: world_api.import_world for '{server_name}', file: '{full_world_file_path}'"
        )
        result = world_api.import_world(
            server_name, full_world_file_path, base_dir
        )  # API func returns dict
        logger.debug(f"API Install World '{server_name}': Handler response: {result}")

        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            success_msg = f"World '{os.path.basename(selected_file_path)}' installed successfully for server '{server_name}'."
            logger.info(f"API: {success_msg}")
            result["message"] = success_msg  # Enhance success message
        else:
            # Handler indicated failure
            status_code = 500
            error_msg = (
                result.get("message", "Unknown world installation error.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(f"API Install World '{server_name}' failed: {error_msg}")
            result = {"status": "error", "message": error_msg}  # Ensure error status

    except (
        FileNotFoundError,
        FileOperationError,
        DownloadExtractError,
        DirectoryError,
        MissingArgumentError,
        InvalidServerNameError,
    ) as e:
        # Catch expected, specific errors from API call chain
        logger.warning(
            f"API Install World '{server_name}': Input/File error: {e}", exc_info=True
        )
        status_code = (
            400 if isinstance(e, (MissingArgumentError, InvalidInputError)) else 500
        )  # 400 for bad client input, 500 for server-side file/config errors
        result = {"status": "error", "message": f"World installation error: {e}"}
    except Exception as e:
        # Catch any unexpected errors during API operation
        logger.error(
            f"API Install World '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"Unexpected error during world installation: {e}",
        }

    return jsonify(result), status_code


# --- API Route: Export World ---
@content_bp.route("/api/server/<string:server_name>/world/export", methods=["POST"])
@csrf.exempt  # Exempt API endpoint from CSRF protection (using JWT or session auth)
@auth_required  # Requires session OR JWT authentication
def export_world_api_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to export the current world of a specified server to a .mcworld file.

    By default, the exported file is saved to the 'worlds' subdirectory
    within the configured CONTENT_DIR.

    Args:
        server_name: The name of the server whose world should be exported (from URL path).

    Returns:
        JSON response indicating success or failure of the world export:
        - 200 OK: {"status": "success", "message": "World '...' exported successfully as '...'.", "export_file": "full/path/to/export.mcworld"}
        - 400 Bad Request: Invalid server name provided.
        - 500 Internal Server Error: World export process failed (e.g., world not found, disk error, CONTENT_DIR missing).
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: World export requested for server '{server_name}' by user '{identity}'."
    )

    # --- Input Validation ---
    # Server name validity is checked within the api_world.export_world function.
    # No request body is expected for this action.

    # --- Call API Handler ---
    result: Dict[str, Any] = {}
    status_code = 500  # Default to internal server error

    try:
        base_dir = (
            get_base_dir()
        )  # May raise FileOperationError if BASE_DIR setting is missing

        # --- Determine Export Directory ---
        # This route overrides the API function's default (BACKUP_DIR)
        # and uses CONTENT_DIR/worlds as the target directory.
        content_dir = settings.get("CONTENT_DIR")
        if not content_dir:
            raise FileOperationError("Required setting 'CONTENT_DIR' is missing.")

        # Define the export directory based on CONTENT_DIR
        api_export_dir = os.path.join(content_dir, "worlds")
        logger.debug(f"API Route: Using export directory: {api_export_dir}")
        # Ensure the target directory exists before calling the API function
        # (The core function also does this, but doing it here provides clearer errors if CONTENT_DIR is bad)
        try:
            os.makedirs(api_export_dir, exist_ok=True)
        except OSError as e:
            raise FileOperationError(
                f"Cannot create export directory '{api_export_dir}': {e}"
            ) from e

        # --- Call the world export API function ---
        logger.debug(
            f"Calling API handler: api_world.export_world for '{server_name}' with explicit export_dir='{api_export_dir}'"
        )
        result = world_api.export_world(
            server_name=server_name,
            base_dir=base_dir,
            export_dir=api_export_dir,  # Explicitly pass the calculated export directory
        )
        logger.debug(f"API Export World '{server_name}': Handler response: {result}")

        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            export_file_path = result.get("export_file", "Unknown Export File")
            filename = os.path.basename(export_file_path)
            success_msg = f"World for server '{server_name}' exported successfully as '{filename}'."
            logger.info(f"API: {success_msg}")
            result["message"] = (
                success_msg  # Update message for better user feedback in response
            )
        else:
            # Handler indicated failure (e.g., couldn't find world name)
            status_code = (
                500  # Assume server-side issue if API layer returns error status
            )
            error_msg = (
                result.get("message", "Unknown world export error.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(f"API Export World '{server_name}' failed: {error_msg}")
            result = {
                "status": "error",
                "message": error_msg,
            }  # Ensure standard error format

    except InvalidServerNameError as e:
        # Catch invalid server name specifically for a 400 response
        logger.warning(
            f"API Export World '{server_name}': Invalid input: {e}", exc_info=False
        )
        status_code = 400
        result = {"status": "error", "message": f"Invalid server name provided: {e}"}
    except FileOperationError as e:
        # Catch errors related to file operations, including missing settings (BASE_DIR, CONTENT_DIR)
        # or inability to create the export directory.
        logger.error(
            f"API Export World '{server_name}': Configuration or File system error: {e}",
            exc_info=True,
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"Configuration or file system error: {e}",
        }
    except (DirectoryError, BackupWorldError) as e:
        # Catch specific, expected errors from the core export process
        logger.error(
            f"API Export World '{server_name}': Error during export process: {e}",
            exc_info=True,
        )
        status_code = 500
        result = {"status": "error", "message": f"World export process error: {e}"}
    except Exception as e:
        # Catch any unexpected errors
        logger.error(
            f"API Export World '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"Unexpected error during world export: {e}",
        }

    return jsonify(result), status_code


# --- Route: Install Addon Selection Page ---
@content_bp.route("/server/<string:server_name>/install_addon")
@login_required  # Requires web session
def install_addon_route(server_name: str) -> Response:
    """
    Renders the page for selecting an addon (.mcaddon or .mcpack file) to install.

    Lists available addon files from the content/addons directory.

    Args:
        server_name: The name of the server to install the addon to (from URL path).

    Returns:
        Rendered HTML page 'select_addon.html' with a list of available addon files.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"User '{identity}' accessed addon install selection page for server '{server_name}'."
    )

    content_dir = os.path.join(settings.get("CONTENT_DIR"), "addons")
    logger.debug(f"Addon content directory: {content_dir}")

    # API call to list available addon files
    allowed_extensions = ["mcaddon", "mcpack"]
    list_result = utils_api.list_content_files(content_dir, allowed_extensions)
    logger.debug(f"List content files API result: {list_result}")

    addon_files: List[str] = []
    if list_result.get("status") == "error":
        error_msg = (
            f"Error listing addon files: {list_result.get('message', 'Unknown error')}"
        )
        flash(error_msg, "error")
        logger.error(
            f"Error listing addon files for server '{server_name}': {error_msg}"
        )
    else:
        addon_files = list_result.get("files", [])

    logger.debug(
        f"Rendering 'select_addon.html' template for server '{server_name}' with {len(addon_files)} files."
    )
    return render_template(
        "select_addon.html",
        server_name=server_name,
        addon_files=addon_files,  # List of full paths to addon files
        app_name=app_name,
    )


# --- API Route: Install Addon ---
@content_bp.route("/api/server/<string:server_name>/addon/install", methods=["POST"])
@csrf.exempt  # API endpoint
@auth_required  # Requires session OR JWT
def install_addon_api_route(server_name: str) -> Tuple[Response, int]:
    """
    API endpoint to install a user-selected addon (.mcaddon or .mcpack file) to a server.

    Expects JSON body with 'filename' key (relative path to addon file in content/addons).

    Args:
        server_name: The name of the server to install the addon to (from URL path).

    JSON Request Body Example:
        {"filename": "/path/relative/to/content/addons/MyAddon.mcaddon"}

    Returns:
        JSON response indicating success or failure of the addon installation:
        - 200 OK: {"status": "success", "message": "Addon '...' installed successfully for server '...'."}
        - 400 Bad Request: Invalid JSON, missing filename, etc.
        - 500 Internal Server Error: Addon installation process failed.
    """
    identity = get_current_identity() or "Unknown"
    logger.info(
        f"API: Addon install requested for server '{server_name}' by user '{identity}'."
    )

    # --- Input Validation ---
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        logger.warning(f"API Install Addon '{server_name}': Invalid/missing JSON body.")
        return (
            jsonify(status="error", message="Invalid or missing JSON request body."),
            400,
        )

    selected_file_path = data.get(
        "filename"
    )  # Expecting *relative* path from selection page
    if not selected_file_path or not isinstance(selected_file_path, str):
        msg = "Missing or invalid 'filename' in request body. Expected relative path to .mcaddon/.mcpack file."
        logger.warning(f"API Install Addon '{server_name}': {msg}")
        return jsonify(status="error", message=msg), 400

    content_base_dir = os.path.join(
        settings.get("CONTENT_DIR"), "addons"
    )  # Base addon dir
    full_addon_file_path = os.path.normpath(
        os.path.join(content_base_dir, selected_file_path)
    )  # Secure path join
    logger.debug(
        f"API Install Addon '{server_name}': Attempting to install from file: {full_addon_file_path}"
    )

    # Security: Ensure path is still within allowed content dir
    if not os.path.abspath(full_addon_file_path).startswith(
        os.path.abspath(content_base_dir)
    ):
        msg = "Invalid filename: Filename must be within the allowed content directory."
        logger.warning(
            f"API Install Addon '{server_name}': {msg} Attempted path: {full_addon_file_path}"
        )
        return jsonify(status="error", message=msg), 400
    if not os.path.isfile(full_addon_file_path):
        msg = f"Selected addon file not found: {full_addon_file_path}"
        logger.warning(msg)
        return jsonify(status="error", message=msg), 404

    # --- Call API Handler ---
    result: Dict[str, Any] = {}
    status_code = 500
    try:
        base_dir = get_base_dir()  # May raise FileOperationError

        # Call the core addon import API function
        logger.debug(
            f"Calling API handler: addon_api.import_addon for '{server_name}', file '{full_addon_file_path}'"
        )
        result = addon_api.import_addon(
            server_name, full_addon_file_path, base_dir
        )  # API function returns dict
        logger.debug(f"API Install Addon '{server_name}': Handler response: {result}")

        if isinstance(result, dict) and result.get("status") == "success":
            status_code = 200
            success_msg = f"Addon '{os.path.basename(selected_file_path)}' installed successfully for server '{server_name}'."
            logger.info(f"API: {success_msg}")
            result["message"] = success_msg  # Enhance success message
        else:
            # Handler indicated failure
            status_code = 500
            error_msg = (
                result.get("message", "Unknown addon installation error.")
                if isinstance(result, dict)
                else "Handler returned unexpected response."
            )
            logger.error(
                f"API Install Addon failed for '{server_name}' (file: '{os.path.basename(selected_file_path)}'): {error_msg}"
            )
            result = {"status": "error", "message": error_msg}  # Ensure error status

    except (
        FileNotFoundError,
        FileOperationError,
        AddonExtractError,
        DirectoryError,
        MissingArgumentError,
        InvalidAddonPackTypeError,
    ) as e:
        # Catch specific, expected errors from API call chain
        logger.warning(
            f"API Install Addon '{server_name}': Input/File error: {e}", exc_info=True
        )
        status_code = (
            400
            if isinstance(
                e, (MissingArgumentError, InvalidInputError, InvalidAddonPackTypeError)
            )
            else 500
        )  # Differentiate client vs server errors
        result = {"status": "error", "message": f"Addon installation error: {e}"}
    except Exception as e:
        # Catch unexpected errors during API operation
        logger.error(
            f"API Install Addon '{server_name}': Unexpected error: {e}", exc_info=True
        )
        status_code = 500
        result = {
            "status": "error",
            "message": f"Unexpected error during addon installation: {e}",
        }

    return jsonify(result), status_code
