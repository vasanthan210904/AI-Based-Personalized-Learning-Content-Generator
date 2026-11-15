"""Saved-material library, private notes and revocable share links."""
from __future__ import annotations

import secrets

from flask import Blueprint, make_response, render_template, request, url_for
from flask_login import current_user

from ..decorators import student_required
from ..extensions import db
from ..models import ContentBookmark, ContentShare, LearningContent, utcnow
from ..utils.responses import api_success
from ..utils.security import get_owned_or_404
from ..utils.serializers import bookmark_dict, content_summary, share_dict
from ..utils.validation import ValidationError, clean_multiline

library_bp = Blueprint("library", __name__)


@library_bp.get("/library/saved")
@student_required
def saved():
    bookmarks = (
        ContentBookmark.query.filter_by(user_id=current_user.id)
        .order_by(ContentBookmark.updated_at.desc())
        .all()
    )
    return render_template(
        "library/saved.html",
        bookmarks=bookmarks,
        notes_count=sum(1 for item in bookmarks if item.note),
    )


@library_bp.get("/shared/<token>")
def shared_view(token: str):
    share = ContentShare.query.filter_by(token=token).first()
    if share is None or share.content is None:
        return (
            render_template(
                "errors/error.html",
                code=404,
                title="Shared material not found",
                message="This share link is invalid or has been revoked by its owner.",
            ),
            404,
        )

    share.views = (share.views or 0) + 1
    share.last_viewed_at = utcnow()
    db.session.commit()
    response = make_response(
        render_template(
            "learning/shared.html",
            content=share.content,
            data=share.content.generated_content or {},
            share=share,
        )
    )
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Cache-Control"] = "private, max-age=60"
    return response


# ----------------------------------------------------------------------
# Bookmarks API
# ----------------------------------------------------------------------
@library_bp.get("/api/bookmarks")
@student_required
def api_list_bookmarks():
    bookmarks = (
        ContentBookmark.query.filter_by(user_id=current_user.id)
        .order_by(ContentBookmark.updated_at.desc())
        .all()
    )
    return api_success({"items": [bookmark_dict(item) for item in bookmarks]})


@library_bp.get("/api/bookmarks/<int:content_id>")
@student_required
def api_bookmark_state(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    bookmark = ContentBookmark.query.filter_by(
        user_id=current_user.id, content_id=content.id
    ).first()
    return api_success(
        {
            "saved": bookmark is not None,
            "content": content_summary(content),
            "bookmark": {
                "note": bookmark.note or "",
                "updated_at": bookmark.updated_at.isoformat() if bookmark else None,
            }
            if bookmark
            else None,
        }
    )


@library_bp.post("/api/bookmarks/<int:content_id>")
@student_required
def api_save_bookmark(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with an optional note.")
    note = clean_multiline(payload.get("note"), 2000) or None
    bookmark = ContentBookmark.query.filter_by(
        user_id=current_user.id, content_id=content.id
    ).first()
    created = bookmark is None
    if bookmark is None:
        bookmark = ContentBookmark(
            user_id=current_user.id, content_id=content.id, note=note
        )
        db.session.add(bookmark)
    elif note is not None:
        bookmark.note = note
    db.session.commit()
    return api_success(
        bookmark_dict(bookmark),
        message="Saved to your library." if created else "Saved material updated.",
        status=201 if created else 200,
    )


@library_bp.put("/api/bookmarks/<int:content_id>")
@student_required
def api_update_bookmark_note(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or "note" not in payload:
        raise ValidationError("Send a JSON object with a note.", "note")
    bookmark = ContentBookmark.query.filter_by(
        user_id=current_user.id, content_id=content.id
    ).first()
    if bookmark is None:
        raise ValidationError("Save this material before adding a note.", "note")
    bookmark.note = clean_multiline(payload.get("note"), 2000) or None
    db.session.commit()
    return api_success(bookmark_dict(bookmark), message="Note saved.")


@library_bp.delete("/api/bookmarks/<int:content_id>")
@student_required
def api_remove_bookmark(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    bookmark = ContentBookmark.query.filter_by(
        user_id=current_user.id, content_id=content.id
    ).first()
    if bookmark is not None:
        db.session.delete(bookmark)
        db.session.commit()
    return api_success({"saved": False}, message="Removed from your library.")


# ----------------------------------------------------------------------
# Share links API
# ----------------------------------------------------------------------
@library_bp.get("/api/learning-content/<int:content_id>/share")
@student_required
def api_share_state(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    share = ContentShare.query.filter_by(content_id=content.id).first()
    return api_success(
        {
            "shared": share is not None,
            "content_id": content.id,
            "title": content.title,
            "share": share_dict(share) if share else None,
        }
    )


@library_bp.post("/api/learning-content/<int:content_id>/share")
@student_required
def api_create_share(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    share = ContentShare.query.filter_by(content_id=content.id).first()
    created = share is None
    if share is None:
        share = ContentShare(
            user_id=current_user.id,
            content_id=content.id,
            token=secrets.token_urlsafe(24),
        )
        db.session.add(share)
        db.session.commit()
    payload = share_dict(share)
    payload["url"] = url_for("library.shared_view", token=share.token)
    return api_success(
        {
            "shared": True,
            "content_id": content.id,
            "title": content.title,
            "share": payload,
        },
        message="Share link created." if created else "Share link already active.",
        status=201 if created else 200,
    )


@library_bp.delete("/api/learning-content/<int:content_id>/share")
@student_required
def api_revoke_share(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    share = ContentShare.query.filter_by(content_id=content.id).first()
    if share is not None:
        db.session.delete(share)
        db.session.commit()
    return api_success({"shared": False}, message="Share link revoked.")
