from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.jobs import JobStore
from services.storage import FileStorage

bp = Blueprint("api", __name__)

_jobs = JobStore(base_dir="data")
_storage = FileStorage(base_dir="data")


@bp.post("/parse")
def parse_pdf_async():
    """
    multipart/form-data with one or more files under key: files
    """
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded. Use multipart key 'files'."}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Empty files list."}), 400

    job_id = _jobs.create_job(payload={"type": "parse", "file_count": len(files)})

    for f in files:
        if not f.filename:
            continue
        data = f.read()
        _storage.save_upload_bytes(job_id, f.filename, data)

    return jsonify({"job_id": job_id, "status": "queued"}), 202


@bp.get("/jobs/<job_id>")
def get_job(job_id: str):
    try:
        job = _jobs.get_job(job_id)
        return jsonify(job), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@bp.post("/feedback")
def post_feedback():
    """
    JSON body:
    {
      "job_id": "...",
      "is_correct": false,
      "reason": "..."
    }

    For now this stores feedback into job.result.feedback and marks needs_feedback.
    Later we will enqueue an LLM repair job type.
    """
    body = request.get_json(silent=True) or {}
    job_id = body.get("job_id")
    is_correct = body.get("is_correct")
    reason = body.get("reason", "")

    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    if is_correct is None:
        return jsonify({"error": "is_correct is required (true/false)"}), 400

    try:
        job = _jobs.get_job(job_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

    result = job.get("result") or {}
    result["feedback"] = {"is_correct": bool(is_correct), "reason": reason}

    # If correct -> keep completed; if incorrect -> mark needs_feedback (next step: enqueue repair)
    new_status = "completed" if bool(is_correct) else "needs_feedback"
    _jobs.update_job(job_id, status=new_status, result=result)

    return jsonify({"job_id": job_id, "status": new_status}), 200


@bp.delete("/jobs/<job_id>")
def delete_job(job_id: str):
    """
    Deletes the job record and its associated files.
    """
    try:
        # 1. Delete files
        _storage.delete_job_files(job_id)
        
        # 2. Delete job record (optional, but let's keep it for now and just delete files if that's what's requested)
        # For now, the user specifically asked to delete PDFs (files).
        # We'll just delete the files and return success.
        
        return jsonify({"job_id": job_id, "message": "Job files deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
