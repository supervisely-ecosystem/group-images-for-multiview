import os
from dotenv import load_dotenv
import numpy as np
import cv2
import imutils
import supervisely as sly
from pyzbar.pyzbar import decode

# load ENV variables for debug
# has no effect in production
load_dotenv(os.path.expanduser("~/supervisely.env"))
load_dotenv("local.env")

check = os.environ["modal.state.XXX"]

def main():
    api = sly.Api.from_env()
    project_id = sly.env.project_id()
    project = api.project.get_info_by_id(project_id)
    if project is None:
        raise KeyError(f"Project with ID {project_id} not found in your account")


if __name__ == "__main__":
    main()
