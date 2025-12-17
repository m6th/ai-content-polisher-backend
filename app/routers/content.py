from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, auth, models
from app.database import get_db

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/polish")
def polish_content(
    request: schemas.ContentRequestCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.credits_remaining <= 0:
        raise HTTPException(status_code=403, detail="Crédits insuffisants")
    
    content_request = crud.create_content_request(db, request, current_user.id)
    
    # 🚀 GÉNÈRE LES FORMATS SELON LE PLAN
    from app.ai_service import polish_content_multi_format
    all_formats, tokens_used = polish_content_multi_format(
        request.original_text,
        request.tone,
        request.language,
        current_user.current_plan
    )
    
    # Sauvegarde tous les formats
    generated_contents = []
    for idx, (format_name, content_text) in enumerate(all_formats.items(), 1):
        generated = crud.create_generated_content(
            db,
            content_request.id,
            content_text,
            variant_number=idx
        )
        generated_contents.append({
            "id": generated.id,
            "format": format_name,
            "content": content_text,
            "created_at": generated.created_at
        })
    
    crud.decrease_user_credits(db, current_user.id)
    crud.create_usage_analytics(db, current_user.id, tokens_used, None)
    
    return {
        "request_id": content_request.id,
        "formats": generated_contents,
        "tokens_used": tokens_used
    }

@router.get("/history")
def get_content_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's content generation history with pagination"""
    query = db.query(models.ContentRequest).filter(
        models.ContentRequest.user_id == current_user.id
    )

    # Search filter
    if search:
        query = query.filter(
            models.ContentRequest.original_text.ilike(f"%{search}%")
        )

    # Total count
    total = query.count()

    # Get paginated results ordered by most recent
    requests = query.order_by(
        models.ContentRequest.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Format response with generated contents
    history_items = []
    for req in requests:
        generated_contents = db.query(models.GeneratedContent).filter(
            models.GeneratedContent.request_id == req.id
        ).all()

        history_items.append({
            "id": req.id,
            "original_text": req.original_text,
            "tone": req.tone,
            "language": req.language,
            "created_at": req.created_at,
            "formats_count": len(generated_contents),
            "generated_contents": [
                {
                    "id": gc.id,
                    "content": gc.polished_text,
                    "variant_number": gc.variant_number
                }
                for gc in generated_contents
            ]
        })

    return {
        "total": total,
        "items": history_items,
        "skip": skip,
        "limit": limit
    }

@router.get("/history/{request_id}")
def get_content_request_detail(
    request_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific content request"""
    content_request = db.query(models.ContentRequest).filter(
        models.ContentRequest.id == request_id,
        models.ContentRequest.user_id == current_user.id
    ).first()

    if not content_request:
        raise HTTPException(status_code=404, detail="Content request not found")

    generated_contents = db.query(models.GeneratedContent).filter(
        models.GeneratedContent.request_id == request_id
    ).all()

    return {
        "id": content_request.id,
        "original_text": content_request.original_text,
        "tone": content_request.tone,
        "language": content_request.language,
        "created_at": content_request.created_at,
        "generated_contents": [
            {
                "id": gc.id,
                "content": gc.polished_text,
                "variant_number": gc.variant_number,
                "created_at": gc.created_at
            }
            for gc in generated_contents
        ]
    }

@router.delete("/history/{request_id}")
def delete_content_request(
    request_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a content request and all its generated contents"""
    content_request = db.query(models.ContentRequest).filter(
        models.ContentRequest.id == request_id,
        models.ContentRequest.user_id == current_user.id
    ).first()

    if not content_request:
        raise HTTPException(status_code=404, detail="Content request not found")

    # Delete all generated contents first (cascade)
    db.query(models.GeneratedContent).filter(
        models.GeneratedContent.request_id == request_id
    ).delete()

    # Delete the request
    db.delete(content_request)
    db.commit()

    return {"message": "Content request deleted successfully"}