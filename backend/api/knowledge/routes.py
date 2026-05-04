"""Knowledge routes: document management, vector search, and KG APIs."""
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.auth.jwt import get_current_user
from backend.db_pg import get_conn, get_dict_cursor
from .knowledge_service import knowledge_service

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class KGSearchRequest(BaseModel):
    query: str
    max_hops: int = 4
    limit: int = 5


@router.get("/list")
def list_documents(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        docs = knowledge_service.list_documents(user_id)
        return {"documents": docs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("help"),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = int(current_user["sub"])

        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        file_bytes = await file.read()
        max_size = 20 * 1024 * 1024
        if len(file_bytes) > max_size:
            raise HTTPException(status_code=400, detail="File size must be <= 20MB")

        valid_categories = {"help", "domain", "log", "faq"}
        if category not in valid_categories:
            category = "help"

        result = knowledge_service.create_document(
            user_id=user_id,
            filename=file.filename,
            file_bytes=file_bytes,
            category=category,
        )

        if background_tasks:
            background_tasks.add_task(_background_vectorize, user_id, result["doc_id"])

        return {
            "message": f"Uploaded {file.filename}, chunked into {result['chunks']} blocks",
            "doc": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback as _tb

        err = _tb.format_exc()
        print(err)
        return JSONResponse(status_code=500, content={"error": str(e), "detail": err})


async def _background_vectorize(user_id: int, doc_id: str):
    try:
        await knowledge_service.vectorize_document(user_id, doc_id)
        print(f"[Knowledge] document {doc_id} vectorized")
    except Exception as e:
        print(f"[Knowledge] vectorize failed for {doc_id}: {e}")


@router.delete("/{doc_id}")
def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        ok = knowledge_service.delete_document(user_id, doc_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Document not found or no permission")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/{doc_id}")
def get_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        doc = knowledge_service.get_document(user_id, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        doc = knowledge_service.get_document(user_id, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        ok = await knowledge_service.vectorize_document(user_id, doc_id)
        if not ok:
            return JSONResponse(status_code=400, content={"error": "Embedding service not configured"})
        return {"ok": True, "message": f"Reindex completed for {doc['name']}"}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/rebuild-index")
async def rebuild_index(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        count = await knowledge_service.rebuild_user_index(user_id)
        return {"ok": True, "message": f"Rebuilt index for {count} chunks"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/search")
async def search_documents(body: SearchRequest, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        results = await knowledge_service.search_documents(user_id, body.query, body.top_k)
        return {"results": results, "query": body.query}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/kg/extract")
async def kg_extract_document(
    doc_id: str = Form(...),
    force: bool = Form(False),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    try:
        doc = knowledge_service.get_document(user_id, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        conn = get_conn()
        cur = get_dict_cursor(conn)
        cur.execute(
            "SELECT COUNT(1) AS c FROM t_knowledge_triple WHERE user_id = %s AND doc_id = %s",
            (user_id, doc_id),
        )
        existed = int((cur.fetchone() or {}).get("c") or 0)
        cur.close()
        conn.close()

        if existed > 0 and not force:
            return {
                "ok": True,
                "skipped": True,
                "message": f"Document {doc_id} already has {existed} extracted relations; skipped. Use force=true to re-extract.",
                "existing_relations": existed,
            }

        if background_tasks:
            background_tasks.add_task(_background_kg_extract, user_id, doc_id)
            return {"ok": True, "message": f"KG extraction task submitted for {doc['name']}"}

        count = await _do_kg_extract(user_id, doc_id)
        return {"ok": True, "message": f"Extraction completed: {count} triples"}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


async def _background_kg_extract(user_id: int, doc_id: str):
    try:
        count = await _do_kg_extract(user_id, doc_id)
        print(f"[KG] document {doc_id} extraction completed: {count} triples")
    except Exception as e:
        print(f"[KG] document {doc_id} extraction failed: {e}")


async def _do_kg_extract(user_id: int, doc_id: str) -> int:
    from .kg_extract_service import kg_extract_service

    conn = get_conn()
    cur = get_dict_cursor(conn)
    cur.execute(
        "SELECT content FROM t_knowledge_chunk WHERE doc_id = %s ORDER BY chunk_index",
        (doc_id,),
    )
    chunks = [row["content"] for row in cur.fetchall()]
    cur.close()
    conn.close()

    if not chunks:
        return 0

    return await kg_extract_service.extract_from_chunks(chunks, user_id, doc_id)


@router.get("/kg/stats")
async def kg_stats(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        from .graph_store import graph_store

        stats = await graph_store.get_stats(user_id)
        return stats
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/kg/search")
async def kg_search(body: KGSearchRequest, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        import re as _re
        from .graph_store import graph_store

        segments = _re.split(r"[，。；：！？\s,.\-;:!?()（）\"'\[\]{}]+", body.query)
        keywords = [s.strip() for s in segments if s.strip() and len(s.strip()) >= 2]
        if not keywords:
            keywords = [body.query.strip()[:20]]
        results = await graph_store.search_paths(user_id, keywords, max_hops=body.max_hops, limit=body.limit)
        return {"results": results, "query": body.query}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/kg/{doc_id}")
async def kg_delete_doc(doc_id: str, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    try:
        from .graph_store import graph_store

        deleted = await graph_store.delete_by_doc(user_id, doc_id)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM t_knowledge_triple WHERE doc_id = %s AND user_id = %s", (doc_id, user_id))
        conn.commit()
        cur.close()
        conn.close()

        return {"ok": True, "deleted_relations": deleted}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
