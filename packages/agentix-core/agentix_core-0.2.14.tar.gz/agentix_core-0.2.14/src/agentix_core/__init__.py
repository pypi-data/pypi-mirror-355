from .v1 import Core, decode_str, decode_dict


__all__ = ["Core", "decode_str", "decode_dict"]

# # Dynamically read version from installed package metadata
# from importlib.metadata import version

# __version__ = version("agentix-core")