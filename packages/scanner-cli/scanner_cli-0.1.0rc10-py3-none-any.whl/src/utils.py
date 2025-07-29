"""Utility functions for the Scanner CLI."""


def format_exception_message(e: Exception, base_msg: str) -> str:
    """Format exception message with better error details for API responses."""
    if hasattr(e, 'args') and len(e.args) > 0:
        response = e.args[0]
        status_code = getattr(response, 'status_code', None)
        status_text = f" (HTTP {status_code})" if status_code else ""
        
        if hasattr(response, 'content'):
            if response.content:
                return f"{base_msg}{status_text}: {response.content!r}"
            else:
                return f"{base_msg}: Empty response{status_text or ' (status code: unknown)'}"
        elif status_code:
            return f"{base_msg}: HTTP {status_code}"
        else:
            return f"{base_msg}: {str(response)}"
    else:
        return f"{base_msg}: {str(e)}"