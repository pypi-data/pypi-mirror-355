import ssl
import os
import math
import socket
import logging
from werkzeug.serving import ThreadedWSGIServer
from typing import Callable
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import transforms3d as t3d
import numpy as np


TF_RUB2FLU = np.array([[0, 0, -1, 0], [-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def get_local_ip():
    try:
        # Connect to an external address (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS as a dummy target
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"


def are_close(a, b=None, lin_tol=1e-9, ang_tol=1e-9):
    """
    Check if two transformation matrices are close to each other within specified tolerances.

    Parameters:
        a (numpy.ndarray): The first transformation matrix.
        b (numpy.ndarray, optional): The second transformation matrix. If not provided, it defaults to the identity matrix.
        lin_tol (float, optional): The linear tolerance for closeness. Defaults to 1e-9.
        ang_tol (float, optional): The angular tolerance for closeness. Defaults to 1e-9.

    Returns:
        bool: True if the matrices are close, False otherwise.
    """
    if b is None:
        b = np.eye(4)
    d = np.linalg.inv(a) @ b
    if not np.allclose(d[:3, 3], np.zeros(3), atol=lin_tol):
        return False
    rpy = t3d.euler.mat2euler(d[:3, :3])
    return np.allclose(rpy, np.zeros(3), atol=ang_tol)


class Teleop:
    """
    Teleop class for controlling a robot remotely.

    Args:
        host (str, optional): The host IP address. Defaults to "0.0.0.0".
        port (int, optional): The port number. Defaults to 4443.
        ssl_context (ssl.SSLContext, optional): The SSL context for secure communication. Defaults to None.
    """

    def __init__(
        self,
        host="0.0.0.0",
        port=4443,
        ssl_context=None,
        natural_phone_orientation_euler=None,
        natural_phone_position=None,
    ):
        self.__logger = logging.getLogger("teleop")
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(logging.StreamHandler())

        self.__server = None
        self.__host = host
        self.__port = port
        self.__ssl_context = ssl_context

        self.__relative_pose_init = None
        self.__absolute_pose_init = None
        self.__previous_received_pose = None
        self.__callbacks = []
        self.__pose = np.eye(4)

        if natural_phone_orientation_euler is None:
            natural_phone_orientation_euler = [0, math.radians(-45), 0]
        if natural_phone_position is None:
            natural_phone_position = [0, 0, 0]
        self.__natural_phone_pose = t3d.affines.compose(
            natural_phone_position,
            t3d.euler.euler2mat(*natural_phone_orientation_euler),
            [1, 1, 1],
        )

        if self.__ssl_context is None:
            self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            self.__ssl_context.load_cert_chain(
                certfile=os.path.join(THIS_DIR, "cert.pem"),
                keyfile=os.path.join(THIS_DIR, "key.pem"),
            )

        self.__app = Flask(__name__)
        self.__app.config['SECRET_KEY'] = 'teleop_secret_key'
        self.__socketio = SocketIO(self.__app, cors_allowed_origins="*")
        
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        self.__register_routes()
        self.__register_socketio_events()

    def set_pose(self, pose: np.ndarray) -> None:
        """
        Set the current pose of the end-effector.

        Parameters:
        - pose (np.ndarray): A 4x4 transformation matrix representing the pose.
        """
        self.__pose = pose

    def subscribe(self, callback: Callable[[np.ndarray, dict], None]) -> None:
        """
        Subscribe to receive updates from the teleop module.

        Parameters:
            callback (Callable[[np.ndarray, dict], None]): A callback function that will be called when pose updates are received.
                The callback function should take two arguments:
                    - np.ndarray: A 4x4 transformation matrix representing the end-effector target pose.
                    - dict: A dictionary containing additional information.
        """
        self.__callbacks.append(callback)

    def __notify_subscribers(self, pose, message):
        for callback in self.__callbacks:
            callback(pose, message)

    def __update(self, message):
        move = message["move"]
        position = message["position"]
        orientation = message["orientation"]

        position = np.array([position["x"], position["y"], position["z"]])
        quat = np.array(
            [orientation["w"], orientation["x"], orientation["y"], orientation["z"]]
        )

        if not move:
            self.__relative_pose_init = None
            self.__absolute_pose_init = None
            self.__notify_subscribers(self.__pose, message)
            return

        received_pose_rub = t3d.affines.compose(
            position, t3d.quaternions.quat2mat(quat), [1, 1, 1]
        )
        received_pose = TF_RUB2FLU @ received_pose_rub
        received_pose[:3, :3] = received_pose[:3, :3] @ np.linalg.inv(
            TF_RUB2FLU[:3, :3]
        )
        received_pose = received_pose @ self.__natural_phone_pose

        # Pose jump protection
        if self.__previous_received_pose is not None:
            if not are_close(
                received_pose,
                self.__previous_received_pose,
                lin_tol=10e-2,
                ang_tol=math.radians(35),
            ):
                self.__logger.warning("Pose jump detected, resetting the pose")
                self.__relative_pose_init = None
                self.__previous_received_pose = received_pose
                return
        self.__previous_received_pose = received_pose

        # Accumulate the pose and publish
        if self.__relative_pose_init is None:
            self.__relative_pose_init = received_pose
            self.__absolute_pose_init = self.__pose
            self.__previous_received_pose = None

        relative_pose = np.linalg.inv(self.__relative_pose_init) @ received_pose
        self.__pose = np.eye(4)
        self.__pose[:3, 3] = self.__absolute_pose_init[:3, 3] + relative_pose[:3, 3]
        self.__pose[:3, :3] = (
            relative_pose[:3, :3] @ self.__absolute_pose_init[:3, :3]
        )

        # Notify the subscribers
        self.__notify_subscribers(self.__pose, message)

    def __register_routes(self):
        @self.__app.route("/<path:filename>")
        def serve_file(filename):
            self.__logger.debug(f"Serving the {filename} file")
            return send_from_directory(THIS_DIR, filename)

        @self.__app.route("/")
        def index():
            self.__logger.debug("Serving the index.html file")
            return send_from_directory(THIS_DIR, "index.html")

    def __register_socketio_events(self):
        @self.__socketio.on('connect')
        def handle_connect():
            self.__logger.info('Client connected')

        @self.__socketio.on('disconnect')
        def handle_disconnect():
            self.__logger.info('Client disconnected')

        @self.__socketio.on('pose')
        def handle_pose(data):
            self.__logger.debug(f"Received pose data: {data}")
            self.__update(data)

        @self.__socketio.on('log')
        def handle_log(data):
            self.__logger.info(f"Received log message: {data}")

    def run(self) -> None:
        """
        Runs the teleop server. This method is blocking.
        """
        self.__logger.info(f"Server started at {self.__host}:{self.__port}")
        self.__logger.info(
            f"The phone web app should be available at https://{get_local_ip()}:{self.__port}"
        )

        self.__server = ThreadedWSGIServer(
            app=self.__app,
            host=self.__host,
            port=self.__port,
            ssl_context=self.__ssl_context,
        )
        self.__server.serve_forever()

    def stop(self) -> None:
        """
        Stops the teleop server.
        """
        if self.__server:
            self.__server.shutdown()
