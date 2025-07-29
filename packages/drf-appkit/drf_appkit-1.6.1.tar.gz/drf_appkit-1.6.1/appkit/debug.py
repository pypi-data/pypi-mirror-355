import inspect
import logging
import os
import traceback

from django.conf import settings


def log(message, level=logging.INFO):
    calling_frame = traceback.extract_stack(limit=2)[0]
    calling_module_path, _ = os.path.splitext(calling_frame.filename)
    relative_module_path = calling_module_path[calling_module_path.index('/app/') + 1:]
    namespace = f"{relative_module_path.replace('/', '.')}.{calling_frame.name}"

    logger = logging.getLogger(namespace)
    logger.log(level, f'{namespace} | {message}')


def trace(message, level=logging.DEBUG, depth=0):
    frames = inspect.stack()

    current_frame = frames[1]
    root_path = str(settings.DJANGO_ROOT_PATH)

    message = '({0}:{1}:{2}): {3}'.format(
        current_frame[1].replace(root_path, ''),
        current_frame[3],
        current_frame[2],
        message,
    )

    if depth > 0:
        for i in range(2, min(depth+2, len(frames))):
            frame = frames[i]
            message += '\n\t{0}, line {1}, in {2}'.format(
                frame[1].replace(root_path, ''),
                frame[2],
                frame[3]
            )

    logger = logging.getLogger("debug")
    logger.log(level, message)
