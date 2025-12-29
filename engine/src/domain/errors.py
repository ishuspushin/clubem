from __future__ import annotations


class GroupOrderAIError(Exception):
    """Base exception for this project."""


class SchemaNotFoundError(GroupOrderAIError):
    pass


class SchemaInvalidError(GroupOrderAIError):
    pass


class PlatformDetectionError(GroupOrderAIError):
    pass


class JobNotFoundError(GroupOrderAIError):
    pass
