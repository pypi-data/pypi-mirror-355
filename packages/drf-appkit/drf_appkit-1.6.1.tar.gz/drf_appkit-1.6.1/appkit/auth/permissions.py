"""This permission system piggybacks on top of the Django Permission system.
Django requires that we associate permissions with specific models. Django also
requires that permissions have a single name, and the namespace is given by the
app name of the model.

This is not flexible enough for our needs.  Rather, we will associate all of our
permissions with the app.models.UserProfile (as that is who this permission system governs)
and we will make a new naming scheme which can be mapped to django's permission name
scheme.

Also, django's permission model's name field is only 50 characters long which is
totally ridiculous. So we will modify that here to be 255 characters which is much
more reasonable.
"""
from collections import defaultdict
import functools
import importlib
import operator

# Monkey patch djangos permission system.
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q

User = get_user_model()

__all__ = [
    'PermissionError',
    'Permission',
]

#-------------------------------------------------------------------------------
class PermissionError(RuntimeError):
    """Raised when a permission is misconfigured.
    """

#-------------------------------------------------------------------------------
class PermissionDoesNotExist(PermissionError):
    """Raised when a permission does not exist
    """

#-------------------------------------------------------------------------------
registered_permissions = {}

#-------------------------------------------------------------------------------
_all_permission_imported = False
def _import_permissions():
    global _all_permission_imported
    if _all_permission_imported:
        return

    from django.apps import apps
    installed_app_names = [app_config.name for app_config in apps.app_configs.values()]
    for app_name in installed_app_names:
        try:
            importlib.import_module("%s.permissions" % app_name)
        except ImportError as e:
            pass
    _all_permission_imported = True

#-------------------------------------------------------------------------------
class Permission(object):
    """Represents a custom permission in the django subsystem.
    """

    #---------------------------------------------------------------------------
    def __init__(self, codename, name, documentation, user_Q_generator=None):
        if codename.count(":") != 1:
            raise PermissionError("The codename for permission MUST be of the form: <subsite>:<permission_name. Yours is: %s" % codename)

        self.app, _ = codename.split(":")
        self.name = name
        self.documentation = documentation
        self.user_Q_generator = user_Q_generator

        self.django_codename = codename
        if not self.django_codename.startswith("app:"):
            django_codename = "app:" + self.django_codename

        # This will be assigned lazily upon first retrieval
        self._django_permission = None

        if self.django_codename not in registered_permissions:
            registered_permissions[self.django_codename] = self

    #---------------------------------------------------------------------------
    def str(self):
        return u"app.Permission(%s)" % (self.codename,)

    #---------------------------------------------------------------------------
    def get_django_permission(self):
        _import_permissions()
        if self._django_permission is None:
            self._django_permission = DjangoPermission.objects.get(
                    content_type=ContentType.objects.get_for_model(User),
                    codename=self.django_codename,
                )
        return self._django_permission
    django_permission = property(get_django_permission)

    #---------------------------------------------------------------------------
    def get_allowed_users_Q(self, user=None):
        """Returns a Q object that identifies the users for this permission.
        """
        if not self.user_Q_generator:
            # A made up query which will always produce zero results.
            return Q(pk__lt=1) & Q(pk__gt=2)
        else:
            return self.user_Q_generator(user)
    allowed_users_Q = property(get_allowed_users_Q)

    #---------------------------------------------------------------------------
    def get_allowed_users(self, user=None):
        """Returns the set of employees that this permission gains access
        to for a given purpose.
        """
        query = self.get_allowed_users_Q(user)
        return User.objects.filter(query).distinct()
    allowed_users = property(get_allowed_users_Q)

    #---------------------------------------------------------------------------
    @staticmethod
    def from_django(django_permission):
        _import_permissions()
        codename = django_permission.codename
        if not codename.startswith("app:"):
            codename = "app:" + codename
        if not codename in registered_permissions:
            raise PermissionDoesNotExist(codename)
        return registered_permissions[codename]

    #---------------------------------------------------------------------------
    def __nonzero__(self):
        """Allow these objects to be used in a boolean context.
        """
        return self.check()

    #---------------------------------------------------------------------------
    def check(self, user=None):
        if user is None:
            return False
        return user.has_perm("core." + self.django_codename)

    #---------------------------------------------------------------------------
    def get_id(self):
        return self.django_permission.id
    id = property(get_id)

    #---------------------------------------------------------------------------
    def required(self):
        def decorator(function):
            def wrapper(request, *args, **kwargs):
                if self.check(request.user):
                    return function(request, *args, **kwargs)
                raise PermissionDenied
            return wrapper
        return decorator

    #---------------------------------------------------------------------------
    def users(self, base_qs=None):
        """ Gets all users that have this permission assigned to their user,
        or belong to a group with this permission
        """
        user_ids = [u.id for u in self.django_permission.user_set.all()]
        for group in self.django_permission.group_set.all():
            user_ids.extend([u.id for u in group.user_set.all()])

        if base_qs is None:
            base_qs = User.objects.all()

        return base_qs.filter(user_id__in=user_ids)

    #---------------------------------------------------------------------------
    def users_and_groups(self, base_qs=None):
        """ Gets the set of users that hold this permission either through
        direct assignment or membership to one or more groups that have it.
        """
        result = []
        for user in self.users(base_qs=base_qs):
            groups = filter(lambda g: self.django_permission in g.permissions.all(), user.groups.all())
            result.append((user, groups))

        return result

    #---------------------------------------------------------------------------
    @staticmethod
    def group_app_permissions(group):
        return [
            Permission.from_django(p)
            for p in group.permissions.filter(codename__startswith="app:")
        ]

    #---------------------------------------------------------------------------
    @staticmethod
    def group_non_app_permissions(group):
        return group.permissions.exclude(codename__startswith="app:")

    #---------------------------------------------------------------------------
    @staticmethod
    def user_app_permissions(user):
        """Gets all of the app permissions that a user has.

        This includes all of the permission they have directly assigned to them
        and all of the permissions they have via a group. It returns it as a
        list of tuples where each tuple contains the permission itself,
        followed by the list of groups that give the permission.
        """

        permissions = set()

        user_permissions = user.user_permissions.filter(
            codename__startswith="app:"
        )
        for permission in user_permissions:
            permissions.add(permission)

        groups = list(user.groups.all())
        for group in groups:
            group_permissions = group.permissions.filter(
                codename__startswith="app:")
            for permission in group_permissions:
                permissions.add(permission)

        return permissions

    #---------------------------------------------------------------------------
    @staticmethod
    def user_non_app_permissions(user):
        """Gets all of the NON-app permissions that a user has.

        This includes all of the permission they have directly assigned to them
        and all of the permissions they have via a group. It returns it as a
        list of tuples where each tuple contains the permission itself,
        followed by the list of groups that give the permission.
        """
        permissions = set()

        user_permissions = user.user_permissions.exclude(
            codename__startswith="app:"
        )
        for permission in user_permissions:
            permissions.add(permission)

        groups = list(user.groups.all())
        for group in groups:
            group_permissions = group.permissions.exclude(
                codename__startswith="app:")
            for permission in group_permissions:
                permissions.add(permission)

        return permissions

    @classmethod
    def model_permissions(cls, content_type):
        model_perms = DjangoPermission.objects.filter(content_type=content_type) \
            .values_list('content_type__app_label', 'codename')
        return {"%s.%s" % (ct, name) for ct, name in model_perms}

    @classmethod
    def user_permissions_by_model(cls, user, model_classes):
        permission_map = defaultdict(set)
        for ModelClass in model_classes:
            content_type = ContentType.objects.get_for_model(ModelClass)
            model_permissions = cls.model_permissions(content_type)
            for permission in model_permissions:
                if user.has_perm(permission):
                    permission_map[content_type.id].add(permission)

        return permission_map


    #---------------------------------------------------------------------------
    @staticmethod
    def all_app_permissions():
        return [
            Permission.from_django(p)
            for p in DjangoPermission.objects.filter(codename__startswith="app:")
        ]


    @staticmethod
    def all_permissions(user):
        """Gets ALL of the permissions that a user has.

        This includes all of the permission they have directly assigned to them
        and all of the permissions they have via a group.
        """
        if user.is_superuser:
            return DjangoPermission.objects.all()

        return user.get_all_permissions()


#-------------------------------------------------------------------------------
class PermissionSet(object):
    """Represents a set of permissions which are permissable for access
    to a given system.

    When you pass in the permissions, pass them in from the most permissive
    to the least permissive. All of these methods are eager, in that they will
    stop processing as soon as they find the first permission the user has
    from the given set.
    """

    #---------------------------------------------------------------------------
    def __init__(self, *permissions, **kwargs):
        self.permissions = permissions

    #---------------------------------------------------------------------------
    def __str__(self):
        return u"app.PermissionSet(%s)" % u"".join([str(p) for p in self.permissions])

    #---------------------------------------------------------------------------
    def __nonzero__(self):
        """Allow these objects to be used in a boolean context.
        """
        return self.check()

    #---------------------------------------------------------------------------
    def check(self, user):
        for permission in self.permissions:
            if isinstance(permission, str):
                if user.has_perm(permission):
                    return True
            elif permission.check(user):
                return True

        return False

    #---------------------------------------------------------------------------
    def required(self):
        def decorator(function):
            def wrapper(request, *args, **kwargs):
                if self.check(request.user):
                    return function(request, *args, **kwargs)
                raise PermissionDenied
            return wrapper
        return decorator

    #---------------------------------------------------------------------------
    def get_allowed_users_Q(self, user=None):
        """Returns a Q objects which identifies the users for this permission.
        """
        allowed_users = []
        for permission in self.permissions:
            if permission.check(user):
                allowed_users.append(permission.get_allowed_users_Q(user=user))

        if not allowed_users:
            return Q(pk__lt=1) & Q(pk__gt=2)
        else:
            return functools.reduce(operator.or_, allowed_users)

    allowed_users_Q = property(get_allowed_users_Q)

    #---------------------------------------------------------------------------
    def get_allowed_users(self, user=None):
        """Returns the set of employees that this permission gains access
        to for a given purpose.
        """
        query = self.get_allowed_users_Q(user)
        return User.objects.filter(query).distinct()
    allowed_users = property(get_allowed_users)
