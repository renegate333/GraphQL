"""Директивы-пермишены @isAuthenticated и @isAdmin."""

from ariadne import SchemaDirectiveVisitor
from graphql import GraphQLError, default_field_resolver


class _BaseDirective(SchemaDirectiveVisitor):
    def _wrap(self, field, check):
        original = field.resolve

        def wrapped(obj, info, **kwargs):
            check(info)
            if original is None:
                return default_field_resolver(obj, info, **kwargs)
            return original(obj, info, **kwargs)

        field.resolve = wrapped
        return field


def _ensure_authenticated(info):
    if not info.context.get("user"):
        raise GraphQLError("Authentication required")


def _ensure_admin(info):
    _ensure_authenticated(info)
    user = info.context.get("user")
    if not getattr(user, "is_admin", False):
        raise GraphQLError("Admin only")


class IsAuthenticatedDirective(_BaseDirective):
    def visit_field_definition(self, field, object_type):
        return self._wrap(field, _ensure_authenticated)


class IsAdminDirective(_BaseDirective):
    def visit_field_definition(self, field, object_type):
        return self._wrap(field, _ensure_admin)