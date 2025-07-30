"""teilen api-definition"""

from typing import Optional
from functools import wraps
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime
from tempfile import TemporaryDirectory
import zipfile
from uuid import uuid4

from flask import Flask, Response, jsonify, request, send_from_directory

from teilen.config import AppConfig


def login_required(password: Optional[str]):
    """Protect endpoint with auth via 'X-Teilen-Auth'-header."""

    def decorator(route):
        @wraps(route)
        def __():
            if request.headers.get("X-Teilen-Auth") != password:
                return Response("FAILED", mimetype="text/plain", status=401)
            return route()

        return __

    return decorator


def register_api(app: Flask, config: AppConfig):
    """Sets up api endpoints."""

    @app.route("/configuration", methods=["GET"])
    def get_configuration():
        """
        Get basic info on configuration.
        """
        return jsonify({"passwordRequired": config.PASSWORD is not None}), 200

    @app.route("/login", methods=["GET"])
    @login_required(config.PASSWORD)
    def get_login():
        """
        Test login.
        """
        return Response("OK", mimetype="text/plain", status=200)

    def get_location(provide_default: bool = True) -> Optional[Path]:
        """Parse and return location-arg."""
        if request.args.get("location") is None:
            if provide_default:
                return config.WORKING_DIR
            return None
        return (
            config.WORKING_DIR / unquote(request.args["location"])
        ).resolve()

    @app.route("/contents", methods=["GET"])
    @login_required(config.PASSWORD)
    def get_contents():
        """
        Returns contents for given location.
        """
        _location = get_location()

        # check for problems
        if (
            config.WORKING_DIR != _location
            and config.WORKING_DIR not in _location.parents
        ):
            return Response("Not allowed.", mimetype="text/plain", status=403)
        if not _location.is_dir():
            return Response(
                "Does not exist.", mimetype="text/plain", status=404
            )

        contents = list(_location.glob("*"))
        folders = filter(lambda p: p.is_dir(), contents)
        files = filter(lambda p: p.is_file(), contents)
        return (
            jsonify(
                [
                    {
                        "type": "folder",
                        "name": f.name,
                        "mtime": f.stat().st_mtime,
                    }
                    for f in folders
                ]
                + [
                    {
                        "type": "file",
                        "name": f.name,
                        "mtime": f.stat().st_mtime,
                        "size": f.stat().st_size,
                    }
                    for f in files
                ]
            ),
            200,
        )

    @app.route("/content", methods=["GET"])
    @login_required(config.PASSWORD)
    def get_content():
        """
        Returns file/folder (as archive) for given location.
        """
        _location = get_location(False)

        if _location is None:
            return Response(
                "Missing 'location' arg.", mimetype="text/plain", status=400
            )

        # check for problems
        if config.WORKING_DIR not in _location.parents:
            return Response("Not allowed.", mimetype="text/plain", status=403)
        if not _location.exists():
            return Response(
                "Does not exist.", mimetype="text/plain", status=404
            )

        if _location.is_file():
            return send_from_directory(
                config.WORKING_DIR,
                _location.relative_to(config.WORKING_DIR),
                as_attachment=True,
            )

        # generate archive in /tmp
        if _location.is_dir():
            with TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir).resolve()
                archive_path = tmp_path / (
                    _location.name + "-" + str(uuid4()) + ".zip"
                )
                print(
                    f"[{datetime.now().isoformat()}] Creating archive "
                    + f"for '{_location.resolve()}' "
                    + f"in '{Path(archive_path).resolve()}'."
                )
                with zipfile.ZipFile(
                    archive_path, "w", zipfile.ZIP_STORED
                ) as archive:
                    for f in _location.glob("**/*"):
                        if f.is_file():
                            archive.write(
                                f,
                                f.resolve().relative_to(
                                    _location.parent.resolve()
                                ),
                            )

                return send_from_directory(
                    tmp_path,
                    archive_path.relative_to(tmp_path),
                    as_attachment=True,
                )

        return Response("Unkown type.", mimetype="text/plain", status=501)
