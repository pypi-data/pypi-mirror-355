#!/usr/bin/env python3

# /// script
# requires-python = ">=3.9"
# ///

import os


project_name = (
    os.environ['PROJECT_NAME']
    .lower()
    .replace(" ", "-")
)
print(project_name, end="")
