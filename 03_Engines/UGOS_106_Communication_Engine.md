\# UGOS DOCUMENT METADATA

Document ID: UGOS\_106\_Communication\_Engine

Version: 1.0.0-DRAFT

Status: APPROVED

Category: Core Engine / Output Formatting

Owner: Core Engineering Architecture Group

Target Audience: Frontend Integrators, API Engineers, UX Designers

Last Updated: 2026-08-09



\---



\# UGOS\_106: Communication Engine Specification



\## 1. PURPOSE

The Communication Engine formats, structures, and streams agent reasoning outputs, code artifacts, and final responses to external clients via REST, WebSocket, or CLI interfaces.



\---



\## 2. RESPONSE PAYLOAD SCHEMA (JSON)



```json

{

&#x20; "task\_id": "TASK-5012",

&#x20; "status": "COMPLETED",

&#x20; "output\_type": "MARKDOWN\_WITH\_ARTIFACTS",

&#x20; "content": "### Analysis Summary\\nTop 5 HTTP 500 errors identified...",

&#x20; "artifacts": \[

&#x20;   {

&#x20;     "artifact\_id": "ART-01",

&#x20;     "type": "JSON",

&#x20;     "filename": "error\_metrics.json",

&#x20;     "payload": "{\\"status\_500\_count\\": 421}"

&#x20;   }

&#x20; ],

&#x20; "confidence\_score": 0.92,

&#x20; "execution\_metrics": {

&#x20;   "total\_duration\_ms": 1420,

&#x20;   "total\_tokens\_used": 1850

&#x20; }

}

3\. STREAMING PROTOCOLFor WebSocket connections, outputs must stream using Server-Sent Events (SSE) / JSON frames with chunk types THINKING, CONTENT\_DELTA, ARTIFACT\_DELTA, and FINAL\_PAYLOAD.4. REVISION HISTORYVersionDateAuthorSummary of Changes1.0.0-DRAFT2026-08-09Core Engineering Architecture GroupInitial Release of Communication Engine Specification

