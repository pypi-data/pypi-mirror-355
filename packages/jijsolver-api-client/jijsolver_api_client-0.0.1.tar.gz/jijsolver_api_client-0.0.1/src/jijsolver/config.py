import os


class JijSolverClientConfig:
    def __init__(self) -> None:
        # Get environment variables
        self.JIJSOLVER_SERVER_HOST = os.getenv("JIJSOLVER_SERVER_HOST")
        self.JIJSOLVER_SERVER_PORT = os.getenv("JIJSOLVER_SERVER_PORT")
        _JIJSOLVER_CLIENT_DEBUG = os.getenv("JIJSOLVER_CLIENT_DEBUG", "False")
        # Set debug mode
        try:
            self.JIJSOLVER_CLIENT_DEBUG = {"true": True, "false": False}[
                _JIJSOLVER_CLIENT_DEBUG.lower()
            ]
        except KeyError:
            raise ValueError("JIJSOLVER_CLIENT_DEBUG must be True or False")
        # Get authentication token
        self.JIJSOLVER_AUTH_TOKEN = os.getenv("JIJSOLVER_ACCESS_TOKEN")
        if self.JIJSOLVER_AUTH_TOKEN is None:
            raise ValueError(
                "Set your access token to the environment variable "
                "`JIJSOLVER_ACCESS_TOKEN`."
            )

    @property
    def debug(self) -> bool:
        return self.JIJSOLVER_CLIENT_DEBUG

    def get_host(self) -> str:
        if self.JIJSOLVER_SERVER_HOST is not None:
            return self.JIJSOLVER_SERVER_HOST
        if self.debug:
            # Local hostname
            return "localhost"
        else:
            raise ValueError(
                "Set API hostname to the environment variable `JIJSOLVER_SERVER_HOST`."
            )

    def get_port(self) -> str:
        if self.JIJSOLVER_SERVER_PORT is not None:
            return str(self.JIJSOLVER_SERVER_PORT)
        else:
            return "443"
