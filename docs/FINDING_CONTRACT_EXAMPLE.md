# Finding Contract Example

```json
{
  "id": "3af3d19a-a915-4a9f-8d72-0a79da9b6ca0",
  "review_id": "58aa6c7a-2789-43fb-8758-5057d36824d7",
  "agent_type": "security",
  "severity": "HIGH",
  "category": "sql-injection",
  "summary": "User-controlled input reaches a raw SQL query without parameterization.",
  "file_path": "backend/app/routes/search.py",
  "line_start": 42,
  "line_end": 46,
  "suggestion": "Use parameterized queries through the repository helper instead of formatting SQL.",
  "confidence": 0.87,
  "rationale": "The diff adds an f-string SQL query using request.query_params['q']; the retrieved repository conventions show all search queries should use bind parameters.",
  "evidence": [
    {
      "source": "retrieval",
      "path": "docs/adr/database-access.md",
      "symbol": null,
      "excerpt": "All SQL must be executed through repository helpers with bind parameters.",
      "rank": 1,
      "metadata": {
        "method": "keyword"
      }
    }
  ],
  "created_at": "2026-07-29T00:00:00Z"
}
```

