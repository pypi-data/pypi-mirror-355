import logging
import os
import plivo
import six
import re

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.http import Http404
from django.views import static
from django.urls import reverse
from django.utils import timezone

from rest_framework.reverse import reverse

SMS_SRC_NUMBER = os.environ.get('PLIVO_SMS_SOURCE_NUMBER')


def get_current_site(request):
    origin = request.META.get("HTTP_ORIGIN")
    if not origin:
        hostname = request.get_host()
        if not hostname:            
            raise Site.DoesNotExist
        origin = f'https://{hostname}'

    url_info = urlparse(origin)
    return Site.objects.get(domain=url_info.netloc)


def site_url_base(site=None):
    scheme = 'http' if settings.DEBUG else 'https'

    if site:
        if site.aliases.exists():
            site = site.aliases.first()
        domain = site.domain
    else:
        domain = settings.TLD
    return f'{scheme}://{domain}'


def public_document_url(document):
    return site_url_base(document.site) + document.get_absolute_url()


# ------------------------------------------------------------------------------
def get_user_agent_ip(request):
    """
    :param request: A django request object possibly containing the originating IP address
    :return: The IP address of the originating request if present, else None
    """
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip_addresses = request.META['HTTP_X_FORWARDED_FOR'].split(',')
        return ip_addresses[0].strip() if ip_addresses else None
    else:
        return request.META.get('REMOTE_ADDR')


def user_initials(user):
    initials = ''

    if user.first_name:
        initials += user.first_name[0]
    if user.last_name:
        initials += user.last_name[0]

    return initials.upper()


def compose_full_name(first_name, last_name):
    full_name = first_name.strip() if first_name else ''
    last_name = last_name.strip() if last_name else ''
    if last_name:
        full_name = full_name + ' ' + last_name
    return full_name


def email_address_for_user(user, verbose=False):
    email_field_name = user.get_email_field_name()
    email_address = getattr(user, email_field_name, None)
    if not email_address:
        if hasattr(user, 'emails') and user.emails.exists():
            email_address = user.emails.first().address

    if not email_address:
        return None

    if verbose:
        email_address = f'{user.get_full_name()} <{email_address}>'

    return email_address



def phone_number_for_user(user):
    try:
        phone = user.profile.phone
        return str(phone) if phone else None
    except AttributeError:
        return None


def base_url(request):
    if not request:
        return settings.BASE_URL

    scheme = 'https' if request.is_secure() else 'http'
    current_site = get_current_site(request)
    domain = current_site.domain

    return '{}://{}'.format(scheme, domain)


def x_sendfile_response(request, path, media_root=settings.MEDIA_ROOT, associated_paths=None):
    if associated_paths and path not in associated_paths:
        raise Http404()

    return static.serve(request, path, document_root=media_root)

    # TODO: Let nginx serve the file
    # Let Apache know it can serve the file.
    # response = HttpResponse()
    # response['X-Sendfile'] = os.path.join(media_root, path)
    #
    # # Remove the default content type that django sets so apache will set it properly.
    # del response['Content-Type']
    # return response


def boolstr(flag):
    return 'TRUE' if flag else 'FALSE'


def bool_from_string(value):
    """Interpret string value as boolean.

    Returns True if value translates to True otherwise False.
    """
    if isinstance(value, six.string_types):
        value = six.text_type(value)
    else:
        msg = "Unable to interpret non-string value '%s' as boolean" % (value)
        raise ValueError(msg)

    value = value.strip().lower()

    if value in ['y', 'yes', 'true', 't', 'on']:
        return True
    elif value in ['n', 'no', 'false', 'f', 'off']:
        return False

    msg = "Unable to interpret string value '%s' as boolean" % (value)
    raise ValueError(msg)


def mimetype_for_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError

    filename, extension = os.path.splitext(path)
    if not extension:
        return None

    extension = extension[1:].lower()

    extension_mimetype_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
    }
    return extension_mimetype_map.get(extension)


def create_date_range_choices():
    now = timezone.now()

    return [{
        'label': 'Past Day',
        'value': 'day',
        'min': (now - relativedelta(days=1)).strftime('%Y-%m-%d'),
    }, {
        'label': 'Past Week',
        'value': 'week',
        'min': (now - relativedelta(weeks=1)).strftime('%Y-%m-%d'),
    }, {
        'label': 'Past Month',
        'value': 'month',
        'min': (now - relativedelta(months=1)).strftime('%Y-%m-%d'),
    }]


def tag_choices(tag_qs, request):
    return [{
        'label': tag.name,
        'purpose': tag.purpose,
        'value': reverse('tag-detail', args=[tag.id], request=request),
    } for tag in tag_qs]


def user_choices(user_qs):
    return [{
        'label': user.full_name,
        'value': str(user.id),
    } for user in user_qs.order_by('username').distinct()]


def userprofile_choices(userprofile_qs):
    return [{
        'label': profile.user.full_name,
        'value': str(profile.id),
    } for profile in userprofile_qs.order_by('user__username').distinct()]


def month_choices(dates=None, date_range=None):
    date_choices = []

    def create_month_choice(lb, ub):
        return {
            'label': lb.strftime('%B %Y'),
            'value': lb.strftime('%Y-%m'),
            'min': lb.strftime('%Y-%m-%d'),
            'max': ub.strftime('%Y-%m-%d')
        }

    if dates:
        current_month = None
        # Establish the unique set of months on which
        # at least one of the given dates falls.
        for d in dates:
            if d.month != current_month:
                start_of_month = date(d.year, d.month, 1)
                next_month = start_of_month + relativedelta(months=1)
                last_of_month = next_month - relativedelta(days=1)
                date_choices.append(create_month_choice(start_of_month, last_of_month))
                current_month = d.month
    elif date_range:
        date_from = date_range[0]
        date_to = date_range[1]
        current_month = date(date_from.year, date_from.month, 1)
        while True:
            next_month = current_month + relativedelta(months=1)
            last_of_month = next_month - relativedelta(days=1)
            date_choices.append(create_month_choice(current_month, last_of_month))

            if next_month >= date_to:
                break
            current_month = next_month

    return date_choices


def month_choices_for_days_past(days_past=365):
    today = timezone.now().date()
    date_range = (today - timedelta(days=days_past), today)
    return reversed(month_choices(date_range=date_range))


def filter_value_list(filter_value_string):
    return filter_value_string.strip().split(',')


image_variation_name_re = re.compile(r"^(\w+)__(.*)$")


def image_variation_size(variation_name, natural_width, natural_height):
    assert natural_width, 'Invalid argument: "natural_width"'
    assert natural_height, 'Invalid argument: "natural_height"'

    if variation_name == 'url':
        return natural_width, natural_height

    width = None
    height = None

    match = image_variation_name_re.match(variation_name)
    if match:
        variation_type = match[1]
        variation_params = match[2]

        if variation_type == 'thumbnail':
            variation_params = variation_params.split('x')
            max_width = int(variation_params[0])
            max_height = int(variation_params[1])

            if natural_width >= natural_height:
                width = max_width
                height = round(natural_height * (max_width / natural_width))
            else:
                height = max_height
                width = round(natural_width * (max_height / natural_height))

    return width, height


def formatted_user_email(user):
    recipient_name = user.get_full_name()
    recipient_email = getattr(user, user.get_email_field_name())
    return f'"{recipient_name}" <{recipient_email}>'


def send_sms(destination, message):
    logger = logging.getLogger("plivo")

    if settings.SMS_DEBUG:
        logger.log(logging.DEBUG, f'Simulated SMS to {destination}:\n{message}\n\n')
        return True
    else:
        with plivo.RestClient() as sms_client:
            try:
                sms_client.messages.create(src=SMS_SRC_NUMBER, dst=destination, text=message)
                logger.log(logging.INFO, f'Sent SMS to {destination}: {message}')
                return True

            except plivo.exceptions.PlivoRestError as e:
                logger = logging.getLogger("plivo")
                logger.log(logging.ERROR, str(e))
                return False


def pagination_links(request, page):
    pagination_querydict = request.GET.copy()
    if 'page' in pagination_querydict:
        del pagination_querydict['page']
    pagination_querystring = pagination_querydict.urlencode()

    paginator = page.paginator

    previous_page = None
    if page.has_previous():
        previous_page = f'?page={page.previous_page_number()}&{pagination_querystring}'.rstrip('&')

    next_page = None
    if page.has_next():
        next_page = f'?page={page.next_page_number()}&{pagination_querystring}'.rstrip('&')

    return {
        'first': f'?page=1&{pagination_querystring}'.rstrip('&'),
        'last': f'?page={paginator.num_pages}&{pagination_querystring}'.rstrip('&'),
        'previous': previous_page or '',
        'next': next_page or '',
    }

