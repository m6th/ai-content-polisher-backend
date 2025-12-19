from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, auth, models
from app.database import get_db
import io
import zipfile
from datetime import datetime

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
    from app.ai_service import polish_content_multi_format, generate_hashtags, generate_ai_suggestions
    from app.plan_config import get_plan_config

    all_formats, tokens_used = polish_content_multi_format(
        request.original_text,
        request.tone,
        request.language,
        current_user.current_plan
    )

    # Récupère les features du plan
    plan_config = get_plan_config(current_user.current_plan)
    hashtags_enabled = plan_config.get('features', {}).get('hashtags', False)
    ai_suggestions_enabled = plan_config.get('features', {}).get('ai_suggestions', False)

    # 🏷️ GÉNÈRE LES HASHTAGS POUR PRO/BUSINESS
    hashtags = []
    if hashtags_enabled:
        # Génère 10-15 hashtags stratégiques
        hashtags = generate_hashtags(
            content=request.original_text,
            language=request.language,
            count=12
        )

    # 💡 GÉNÈRE LES SUGGESTIONS D'AMÉLIORATION POUR PRO/BUSINESS
    ai_suggestions = None
    if ai_suggestions_enabled:
        ai_suggestions = generate_ai_suggestions(
            content=request.original_text,
            language=request.language
        )
    
    # Sauvegarde tous les formats avec leurs variantes
    generated_contents = []
    variant_counter = 1

    for format_name, content_data in all_formats.items():
        # Si content_data est une liste (plusieurs variantes), traiter chacune
        if isinstance(content_data, list):
            for variant_idx, content_text in enumerate(content_data, 1):
                generated = crud.create_generated_content(
                    db,
                    content_request.id,
                    content_text,
                    variant_number=variant_counter,
                    format_name=format_name
                )
                generated_contents.append({
                    "id": generated.id,
                    "format": format_name,
                    "variant": variant_idx,
                    "content": content_text,
                    "created_at": generated.created_at
                })
                variant_counter += 1
        else:
            # Une seule variante (plans Free/Starter)
            generated = crud.create_generated_content(
                db,
                content_request.id,
                content_data,
                variant_number=variant_counter,
                format_name=format_name
            )
            generated_contents.append({
                "id": generated.id,
                "format": format_name,
                "variant": 1,
                "content": content_data,
                "created_at": generated.created_at
            })
            variant_counter += 1
    
    crud.decrease_user_credits(db, current_user.id)
    crud.create_usage_analytics(db, current_user.id, tokens_used, None)

    return {
        "request_id": content_request.id,
        "formats": generated_contents,
        "hashtags": hashtags if hashtags_enabled else None,
        "ai_suggestions": ai_suggestions,
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

@router.get("/export/{request_id}")
def export_all_formats(
    request_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Export all generated formats as a ZIP file (Pro/Business only)"""
    from app.plan_config import get_plan_config

    # Check if user has bulk export feature
    plan_config = get_plan_config(current_user.current_plan)
    bulk_export_enabled = plan_config.get('features', {}).get('bulk_export', False)

    if not bulk_export_enabled:
        raise HTTPException(
            status_code=403,
            detail="L'export en masse est réservé aux plans Pro et Business"
        )

    # Get the content request
    content_request = db.query(models.ContentRequest).filter(
        models.ContentRequest.id == request_id,
        models.ContentRequest.user_id == current_user.id
    ).first()

    if not content_request:
        raise HTTPException(status_code=404, detail="Content request not found")

    # Get all generated contents
    generated_contents = db.query(models.GeneratedContent).filter(
        models.GeneratedContent.request_id == request_id
    ).all()

    if not generated_contents:
        raise HTTPException(status_code=404, detail="No generated content found")

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Group contents by format for counting variants
        formats_count = {}
        for gc in generated_contents:
            format_key = gc.format_name or f"format_{gc.variant_number}"
            if format_key not in formats_count:
                formats_count[format_key] = 0
            formats_count[format_key] += 1

            # Create descriptive filename
            variant_suffix = f"_variant_{formats_count[format_key]}" if formats_count[format_key] > 1 else ""
            filename = f"{format_key}{variant_suffix}.txt"

            # Add content to zip
            zip_file.writestr(
                filename,
                gc.polished_text
            )

        # Add metadata file
        metadata = f"""Content Export - AI Content Polisher
================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Original Text:
{content_request.original_text}

Settings:
- Tone: {content_request.tone}
- Language: {content_request.language}

Generated Formats:
{chr(10).join([f'- {fmt}: {count} variant(s)' for fmt, count in formats_count.items()])}

Total Files: {len(generated_contents)}
"""
        zip_file.writestr("_README.txt", metadata)

    # Prepare response
    zip_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=content_export_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        }
    )