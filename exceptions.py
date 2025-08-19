#!/usr/bin/env python3

class EAConnectorError(Exception):
    """Custom exception for EA Connector errors."""
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

    def to_dict(self):
        return {
            "error": self.args[0],
            "details": self.details or "No additional details provided."
        }
