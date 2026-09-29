"""Резолверы GraphQL (Query и Mutation)."""

import json
import uuid

from ariadne import MutationType, QueryType
from fastapi import HTTPException
from sqlalchemy import or_

from app.audit.service import write_event
from app.core.jwt import create_access_token
from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
)
from app.models import AuditEvent, OAuthClient, User

query = QueryType()
mutation = MutationType()


# ---------- helpers ----------

def _iso(dt):
    return dt.isoformat() if dt else None


def _user_to_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "isActive": u.is_active,
        "isAdmin": u.is_admin,
        "createdAt": _iso(u.created_at),
    }


def _client_to_dict(c: OAuthClient) -> dict:
    return {
        "id": str(c.id),
        "clientId": c.client_id,
        "name": c.name,
        "isConfidential": c.is_confidential,
        "redirectUris": c.redirect_uris or [],
        "createdAt": _iso(c.created_at),
    }


def _audit_to_dict(e: AuditEvent) -> dict:
    return {
        "id": str(e.id),
        "eventType": e.event_type,
        "actorId": e.actor_id,
        "ip": e.ip,
        "userAgent": e.user_agent,
        "metadata": json.dumps(e.metadata_json) if e.metadata_json else None,
        "createdAt": _iso(e.created_at),
    }


# ---------- Query ----------

@query.field("me")
def resolve_me(_, info):
    return _user_to_dict(info.context["user"])


@query.field("users")
def resolve_users(_, info, search=None, limit=50, offset=0):
    db = info.context["db"]
    q = db.query(User)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(User.email.ilike(like)))
    q = q.offset(offset).limit(limit)
    return [_user_to_dict(u) for u in q.all()]


@query.field("clients")
def resolve_clients(_, info):
    db = info.context["db"]
    return [_client_to_dict(c) for c in db.query(OAuthClient).all()]


@query.field("auditEvents")
def resolve_audit_events(_, info, eventType=None, limit=50, offset=0):
    db = info.context["db"]
    q = db.query(AuditEvent)
    if eventType:
        q = q.filter(AuditEvent.event_type == eventType)
    q = q.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
    return [_audit_to_dict(e) for e in q.all()]


# ---------- Mutation ----------

@mutation.field("registerUser")
def resolve_register_user(_, info, email, password):
    db = info.context["db"]
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        validate_policy(password, user_inputs=[email])
    except WeakPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    write_event(
        db,
        event_type="user.created",
        actor_id=user.id,
        metadata={"email": user.email, "source": "graphql"},
    )

    token = create_access_token(sub=user.email)
    return {"accessToken": token, "tokenType": "bearer"}


@mutation.field("createClient")
def resolve_create_client(_, info, name, isConfidential=True):
    db = info.context["db"]
    client = OAuthClient(
        client_id=uuid.uuid4().hex,
        name=name,
        is_confidential=isConfidential,
        redirect_uris=[],
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    actor = info.context.get("user")
    write_event(
        db,
        event_type="client.created",
        actor_id=actor.id if actor else None,
        client_id=client.client_id,
        metadata={"name": client.name},
    )
    return _client_to_dict(client)


@mutation.field("disableUser")
def resolve_disable_user(_, info, userId):
    db = info.context["db"]
    user = db.query(User).filter(User.id == int(userId)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    actor = info.context.get("user")
    write_event(
        db,
        event_type="user.disabled",
        actor_id=actor.id if actor else None,
        metadata={"target_user_id": user.id, "target_email": user.email},
    )
    return _user_to_dict(user)