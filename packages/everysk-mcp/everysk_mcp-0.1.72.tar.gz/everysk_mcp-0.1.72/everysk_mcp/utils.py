###############################################################################
#
# (C) Copyright 2025 EVERYSK TECHNOLOGIES
#
# This is an unpublished work containing confidential and proprietary
# information of EVERYSK TECHNOLOGIES. Disclosure, use, or reproduction
# without authorization of EVERYSK TECHNOLOGIES is prohibited.
#
###############################################################################
import base64


###############################################################################
# Implementation
###############################################################################
def from_utf8_to_base64(data: str) -> str:
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def from_base64_to_utf8(data: str) -> str:
    return base64.b64decode(data.encode('utf-8')).decode('utf-8')

