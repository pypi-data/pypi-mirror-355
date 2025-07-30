from django.db.models.fields import BLANK_CHOICE_DASH


def img_src(media_attachment, size):
    image = media_attachment.image

    if not media_attachment.warm:
        return image.url

    try:
        return image.thumbnail[size].url
    except KeyError:
        return image.url


def to_choices(values, key=None, include_blank=True):
    choices = [(
        value[key] if key else value,
        value
    ) for value in values]

    if include_blank:
        choices.insert(0, ("", "---------"))

    return choices


def to_choice_info_list(choice_list, nullable=False):
    choices = []
    for item in choice_list:
        if isinstance(item, tuple):
            choice = {'value': str(item[0]), 'label': str(item[1])}
        else:
            choice = {'value': str(item), 'label': str(item)}
        choices.append(choice)

    if nullable:
        choices.insert(0, { 'label': '--- None ---', 'value': 'null' })

    return choices


def split_full_name(full_name):
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        return first_name, last_name
    else:
        return full_name, None

def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = str(val).lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    if val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    raise ValueError(f"invalid truth value {val!r}")
