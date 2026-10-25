# Quickstart: import a ChatGPT export and query it

From zero to querying your own conversation history in four steps. All examples talk to the Gateway (default `http://127.0.0.1:8000`); start it as described in [gateway/README.md](../gateway/README.md) with `EVIDENCE_READ_API_TOKEN` set.

## 1. Start the Gateway

```bash
cd gateway
cp .env.example .env   # set the three secrets and DATABASE_URL
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 2. Upload a ChatGPT export

`POST /import/chatgpt` takes the export as a ZIP (202 Accepted; the import runs in the background):

```bash
curl -s -X POST http://127.0.0.1:8000/import/chatgpt \
  -F "file=@chatgpt-export.zip"
```

Sample response:

```json
{"import_job_id": "3f9c2a54-8f21-4d1e-9c66-3f6e88a1b2d4"}
```

The file must end in `.zip` (415 otherwise) and stays under the upload limit (413).

## 3. Poll the import job

```bash
curl -s http://127.0.0.1:8000/import-jobs/3f9c2a54-8f21-4d1e-9c66-3f6e88a1b2d4
```

Sample response:

```json
{
  "import_job_id": "3f9c2a54-8f21-4d1e-9c66-3f6e88a1b2d4",
  "status": "completed",
  "result_code": null,
  "error_code": null,
  "progress": {},
  "counts": {"discovered": 128, "imported": 128, "skipped": 0, "failed": 0},
  "errors": {},
  "report": null
}
```

Poll until the run finishes; `counts.imported` is what landed. (`POST /import-jobs/{job_id}/retry` exists for failed jobs.)

## 4. Query the conversations

`GET /api/v1/evidence/conversation-observations` with the evidence read token as a Bearer token:

```bash
curl -s -H "Authorization: Bearer $EVIDENCE_READ_API_TOKEN" \
  "http://127.0.0.1:8000/api/v1/evidence/conversation-observations?limit=5"
```

Sample response (an `ObservationPage`; `next_cursor` continues the list):

```json
{
  "kind": "conversation-observations",
  "items": [
    {
      "conversation_id": "8f0a1b2c-...",
      "source_account_id": "1a2b3c4d-...",
      "title": "Discussion about caching strategies",
      "created_at": "2026-09-14T10:22:31Z"
    }
  ],
  "next_cursor": null
}
```

`source_account_id`, `conversation_id` and `cursor` filter and page; every response carries `kind: "conversation-observations"`.

---

Every endpoint above lives in `gateway/app` (`api_import.py`, `api_evidence.py`); if a request shape surprises you, the handler is the source of truth.
