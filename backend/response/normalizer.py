import re

class ResponseNormalizer:
    """Cleans and normalizes the response text."""
    def normalize(self, content: str) -> str:
        # Strip trailing whitespaces
        content = content.strip()
        # Normalize line endings
        content = content.replace("\r\n", "\n")
        # Remove weird non-printable characters if necessary
        # content = re.sub(r'[^\x00-\x7F]+', '', content)
        return content
