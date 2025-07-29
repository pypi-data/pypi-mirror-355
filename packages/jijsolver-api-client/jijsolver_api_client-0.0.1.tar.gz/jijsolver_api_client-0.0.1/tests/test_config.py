from unittest import mock

from src.jijsolver.config import JijSolverClientConfig


def test_default():
    with mock.patch.dict(
        "os.environ",
        {
            "JIJSOLVER_ACCESS_TOKEN": "test_token",
            "JIJSOLVER_SERVER_HOST": "test.example.com",
        },
    ):
        config = JijSolverClientConfig()
        assert not config.debug
        assert config.get_host() == "test.example.com"
        assert config.get_port() == "443"


def test_set_host_and_port():
    with mock.patch.dict(
        "os.environ",
        {
            "JIJSOLVER_ACCESS_TOKEN": "test_token",
            "JIJSOLVER_SERVER_HOST": "aaa.com",
            "JIJSOLVER_SERVER_PORT": "8888",
        },
    ):
        config = JijSolverClientConfig()
        assert not config.debug
        assert config.get_host() == "aaa.com"
        assert config.get_port() == "8888"


def test_debug():
    with mock.patch.dict(
        "os.environ",
        {
            "JIJSOLVER_CLIENT_DEBUG": "True",
            "JIJSOLVER_ACCESS_TOKEN": "test_token",
        },
    ):
        config = JijSolverClientConfig()
        assert config.debug
        assert config.get_host() == "localhost"
        assert config.get_port() == "443"


def test_debug_and_set_host_and_port():
    with mock.patch.dict(
        "os.environ",
        {
            "JIJSOLVER_CLIENT_DEBUG": "True",
            "JIJSOLVER_SERVER_HOST": "aaa.com",
            "JIJSOLVER_SERVER_PORT": "8888",
            "JIJSOLVER_ACCESS_TOKEN": "test_token",
        },
    ):
        config = JijSolverClientConfig()
        assert config.debug
        assert config.get_host() == "aaa.com"
        assert config.get_port() == "8888"
