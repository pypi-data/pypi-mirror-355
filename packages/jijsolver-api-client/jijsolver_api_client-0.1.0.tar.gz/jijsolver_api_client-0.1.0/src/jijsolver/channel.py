import ssl

import grpc
from grpc._channel import Channel


def ssl_channel_manager(target: str) -> Channel:
    try:
        ssl_defaults = ssl.get_default_verify_paths()
        credentials = grpc.ssl_channel_credentials(
            ssl.create_default_context().load_verify_locations(
                cafile=ssl_defaults.cafile
            )
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load certs: {e}")

    return grpc.secure_channel(target, credentials)


def no_ssl_channel_manager(target: str) -> Channel:
    return grpc.insecure_channel(target)
