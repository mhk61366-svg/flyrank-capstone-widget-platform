# BUILDLOG — Embeddable Widget & Lead-Capture Platform

## 1. Overview

This document records how I built the Embeddable Widget & Lead-Capture Platform during the FlyRank Backend Internship, including where I used AI assistance, what work I implemented myself, and how I used AI during debugging and development.

The project was built according to the four phases defined in the FlyRank capstone brief:

1. Phase 1 — Design
2. Phase 2 — The Hardened Submission Path
3. Phase 3 — Delivery, Dashboard & Proof
4. Phase 4 — Demo Preparation

Rather than asking AI to build the complete project, I used Claude primarily as a learning and development assistant. At the beginning of each phase, I asked Claude to break the phase down into smaller stages and provide a detailed guide explaining what I needed to build, why each component was needed, and how the pieces connected. I then followed those stages and implemented the project incrementally.

When I encountered errors or concepts I did not understand, I used Claude to explain the problem, debug the issue, and help me determine the appropriate correction.

The resulting architecture and major implementation decisions were my own. The core API routes, service layer, repository layer, Docker configuration, and evidence collection were implemented by me.

---

# 2. Development Approach

## 2.1 AI-assisted learning workflow

My general workflow throughout the project was:

1. Identify the requirements for the current phase.
2. Ask Claude to break the phase into manageable development stages.
3. Read and understand the guide before implementing anything.
4. Implement the stage myself or wire the provided code into my project where AI assistance was used.
5. Run the application/tests.
6. When an error occurred that I could not understand, provide the error or screenshot to Claude.
7. Use Claude's explanation to understand the cause and apply the fix.
8. Continue to the next stage.
9. Review the resulting implementation rather than blindly accepting generated code.

This approach was particularly useful because the capstone contained several concepts that were new or more complex than the earlier internship assignments, including public cross-origin requests, rate limiting, geo-enrichment fallback, spam protection, and failure-tolerant side effects.

---

# 3. Phase 1 — Design

## Objective

The first phase was focused on understanding the complete system before writing the main implementation.

The FlyRank brief required a system in which an authenticated tenant could create a widget, obtain an embed snippet, receive submissions from an external website, and expose those submissions through a dashboard API. The system also needed validation, CORS, rate limiting, spam protection, geo-enrichment with fallback, persistence, and safe side effects.

### My work

The overall architecture and design decisions were mine.

I determined how the application should be structured into:

* FastAPI routes
* Service layer
* Repository layer
* PostgreSQL
* Supabase authentication
* Public widget delivery
* Public submission processing

I also decided the boundaries between the layers and what responsibilities belonged in each one.

The final architecture follows:

`routes → services → repositories → PostgreSQL`

with business logic kept out of the repository layer and SQL kept out of the service layer.

### AI assistance

I used Claude to help turn my requirements and design decisions into formal documentation.

I explained to Claude what I wanted the system to contain and how I wanted it structured. Claude then helped produce the initial versions of documentation such as:

* `DESIGN.md`
* `README.md`
* `capstone.yaml`

I reviewed these documents and edited them where necessary. Therefore, the final documents were not accepted blindly as AI output.

The architecture itself was not delegated to Claude. I provided the intended architecture and requirements, while Claude helped formalize them into documentation.

### Result

The design phase produced the data model, API surface, layer structure, public submission flow, and explicit non-goals that were then used as the basis for implementation.

The final design uses Supabase Auth as the identity source rather than creating a local users/tenants table. The authenticated Supabase user's UUID is used as `tenant_id` in the application's tables.

---

# 4. Phase 2 — The Hardened Submission Path

This was the most technically involved phase because the public submission endpoint accepts requests from websites outside the application's control.

The main flow became:

`validation → rate limiting → spam check → geo enrichment → storage → notification`

The important requirement was that failures in non-critical components should not prevent a valid submission from being stored.

## 4.1 Supabase authentication

### My work

I had already learned the fundamentals of Supabase authentication, JWTs, and project configuration earlier in the internship.

I implemented the authentication flow and integrated it with the application.

### AI assistance

Claude helped me understand the reasoning behind using the Supabase authenticated user's ID directly as the tenant ID.

The important concept was that the project did not maintain its own local users table. Supabase Auth already owns the user identity, so the verified `user.id` from the JWT could be used as the application's `tenant_id`.

Claude helped explain this relationship and assisted with portions of the implementation. Some of the code was written by me and some was generated with Claude's assistance, after which I wired it into the project and verified that I understood what it was doing.

The final design explicitly enforces tenant isolation by taking `tenant_id` from the verified JWT rather than accepting it from the client.

---

## 4.2 Geo enrichment

### My work

I read the quickstart/documentation for the geo providers before implementing the feature.

The final fallback chain is:

`ip-api.com → ipapi.co → no geo`

The important behavior is that geo-enrichment is not allowed to break the submission. If both providers fail, the submission is still stored without geo information.

### AI assistance

Claude helped me with the implementation and correction of the geo-enrichment code.

My process was to first read the provider documentation and understand the intended API usage, then implement it, and use Claude when the implementation needed correction or debugging.

I did not treat the generated code as something to copy without understanding. Claude's explanations helped me understand the provider calls, the fallback sequence, and why the main submission path needed to continue even when enrichment failed.

---

## 4.3 Rate limiting

### My work

The final implementation uses in-memory, per-IP rate limiting.

I implemented the rate-limiting logic myself.

### AI assistance

Claude explained that an in-memory IP-based limiter was the simplest and most time-efficient solution for the capstone, especially because I was approaching the end of the project and needed to prioritize the required functionality.

Claude explained the approach and the code involved. I understood the approach from the explanation and implemented the rate limiter myself.

Later, Claude helped me debug issues involving `429 Too Many Requests` responses and the burst test.

The final implementation intentionally uses per-IP in-memory limiting rather than a distributed rate-limiting store. This is documented as a project limitation because the state resets when the API restarts.

---

## 4.4 Honeypot spam protection

### My work

The project uses a honeypot field as its spam-prevention mechanism.

### AI assistance

Claude recommended the honeypot approach because it was simple and appropriate for the scope of the capstone.

Claude explained how the technique worked and why a hidden field that legitimate users leave empty could be used to identify automated submissions.

After understanding the approach, I used the provided implementation code and wired it into my submission flow.

The final design uses the honeypot as the project's required spam-control mechanism.

---

## 4.5 CORS and browser security

### My work

I integrated the CORS behavior into the application and tested the public submission endpoint from an external origin.

### AI assistance

CORS was one of the areas where I relied heavily on Claude for debugging.

When the browser and terminal produced errors, I provided the errors/screenshots to Claude. It explained what the errors meant and what needed to be changed.

During testing, I encountered issues involving:

* the allowed-origin configuration
* a trailing-slash mismatch in `ALLOWED_ORIGINS`
* middleware ordering
* Chrome's Private Network Access behavior when a hosted page attempted to communicate with a localhost API

Claude helped identify these problems and explain the required changes.

The final implementation includes the additional handling required for the Private Network Access behavior, and the README documents both the origin mismatch and middleware-ordering problems that were found and corrected during testing.

This was a useful example of AI being used primarily as a debugging and explanation tool rather than simply as a code generator.

---

# 5. Phase 3 — Delivery, Dashboard & Proof

Phase 3 covered the widget delivery system, dashboard endpoints, testing, and project documentation.

## 5.1 API routes

### My work

The API routes were built by me.

This includes the authenticated widget-management routes and the public widget/submission routes.

The final API includes:

* `POST /widgets`
* `GET /widgets`
* `GET /widgets/{id}`
* `PATCH /widgets/{id}`
* `DELETE /widgets/{id}`
* `GET /widgets/{id}/submissions`
* `GET /widgets/{id}/stats`
* `GET /widgets/{id}/config`
* `GET /widget.js`
* `POST /submissions`
* `OPTIONS /submissions`

These routes correspond to the three request paths defined during the design: authenticated owner operations, public widget delivery, and public submission.

Claude did not build these routes for me. I implemented the route layer myself.

---

## 5.2 Service layer

The service layer was implemented by me.

I was responsible for deciding which business operations belonged in the services and how the different components interacted.

The final service layer keeps SQL out of business logic and coordinates operations such as validation, rate limiting, spam checking, geo enrichment, notification, and persistence.

The layer separation follows the architecture established during Phase 1.

---

## 5.3 Repository layer

The repository layer was also implemented by me.

I wrote the database interaction and raw SQL using `psycopg`, rather than using an ORM.

The repository layer is responsible for persistence while the service layer handles the business logic.

This separation was one of my own architectural decisions.

---

## 5.4 Widget delivery and dashboard

I implemented the widget delivery and dashboard-related functionality as part of the project.

The public configuration endpoint provides a small cached configuration response, while the widget JavaScript is served separately.

The dashboard API provides submission data and basic statistics including counts, daily information, and geographic breakdowns.

The widget itself was tested from a different origin so that the project demonstrated the actual cross-origin behavior required by the capstone rather than only testing requests from the API's own origin.

---

# 6. Testing and Debugging

Automated testing was an area where Claude was useful primarily for debugging.

I wrote and ran the project's tests, and when pytest produced terminal errors that I could not immediately understand, I provided screenshots/errors to Claude.

Claude diagnosed the errors, explained what was wrong, and guided me toward the fixes.

### AI-assisted debugging

The debugging process generally followed:

`pytest → error → inspect output → provide error to Claude → understand cause → modify implementation → rerun tests`

This was especially useful for the more complex cases involving:

* CORS
* rate limiting and `429` responses
* burst behavior
* middleware interaction
* automated test failures
* service integration

### Test coverage improvements

Claude's initial testing guidance focused heavily on the technically important/scary cases and their expected outcomes.

However, during review I noticed that some more general/basic tests were missing.

I added those tests myself.

This is an example where I did not simply follow the AI-generated plan as complete. I reviewed the proposed testing scope against the actual project requirements and expanded it where I considered it insufficient.

---

# 7. Documentation

Claude assisted with producing the initial versions of the project's documentation.

The main documents involved were:

* `README.md`
* `DESIGN.md`
* `capstone.yaml`

### Process

My process was:

1. Decide what the document needed to contain.
2. Explain the desired structure/content to Claude.
3. Have Claude produce a draft.
4. Review the generated document.
5. Correct or edit anything that did not accurately represent my project.
6. Use the resulting document in the repository.

Therefore, while Claude generated substantial portions of the initial Markdown documents, the final versions were reviewed and edited by me.

### EVIDENCE.md

`EVIDENCE.md` was different.

I created `EVIDENCE.md` myself.

I collected and organized the evidence required to demonstrate that the Definition-of-Done requirements were actually working. I did not delegate the creation of this file to Claude.

---

# 8. Docker and Project Infrastructure

The Docker configuration was implemented by me.

I created:

* `Dockerfile`
* `docker-compose.yml`

The containerized setup is used to run the API and its required infrastructure, and the documented startup command is:

`docker compose up -d --build`

The repository's `capstone.yaml` records this as the project's run command.
Claude did not build these Docker files for me.
Apart from that debugging assistance, the Docker configuration was my own work.

---

# 9. Examples of AI-Assisted Corrections

## 9.1 CORS configuration

An origin configuration problem caused the browser's actual `Origin` value not to match the configured allowed origin because of a trailing-slash mismatch.

Claude helped identify the mismatch and explain why the browser rejected the request.

I corrected the configuration.

---

## 9.2 CORS middleware ordering

The Private Network Access handling initially could not be reached correctly because of middleware ordering.

Claude helped diagnose why the expected middleware behavior was not occurring.

I corrected the ordering so the required preflight behavior could be handled.

---

## 9.3 Rate-limit debugging

During rate-limit testing, I encountered issues around the expected `429` responses and burst behavior.

Claude helped me interpret the test results and identify what needed to be changed.

I applied the fixes and continued testing.

---

## 9.4 Automated test failures

Some pytest failures produced errors that I could not understand from the terminal output alone.

I sent screenshots/errors to Claude.

Claude explained what the errors meant and what was causing them. I then made the required corrections and reran the tests.

---

## 9.5 Client IP rejected by Postgres under automated tests

TestClient doesn't make a real network connection, so request.client.host returned the literal string "testclient" instead of a real IP. The submissions.ip_address column is typed inet, which rejected that string outright and caused three tests to fail with a database-layer error instead of an application-logic one.

Claude helped trace the failure back to the inet type validation rather than the submission logic itself.

I added safe_ip() in app/services/submission_service.py, which validates the incoming value and returns None for anything that isn't a real IP before it reaches the repository layer. See EVIDENCE.md, Abuse Protection & Spam Control (2c).

---

## 9.6 Cache-Control header dropped on widget.js
GET /widget.js appeared to set a Cache-Control header in code, but the header was missing from actual responses. FastAPI's pattern of injecting a Response object and mutating response.headers[...] only takes effect when the route returns plain data that FastAPI wraps itself — get_widget_js instead constructed and returned its own Response object directly, so the injected parameter's header mutation was never applied.

Claude helped me understand why the two patterns behave differently.

I fixed it by passing the headers directly into the returned Response(...) constructor. See EVIDENCE.md, Widget Delivery (3a).

---

9.7 Tenant-identity leakage between dashboard test fixtures

dependency_overrides on get_current_tenant_id is a single dictionary shared by the whole app object, not scoped per TestClient. The original tenant-A/tenant-B fixtures set this override and only cleared it at teardown, so tests needing two different tenant identities in the same test saw one identity silently leak into the other — two dashboard isolation tests incorrectly returned 200 instead of 401/404.

Claude helped me trace the false-pass back to override lifecycle rather than the endpoint logic.

I replaced the fixtures with an as_tenant(tenant_id) context manager in conftest.py that sets and clears the override immediately around each request. See EVIDENCE.md, Dashboard API (3d).

# 10. What I Built Myself vs. AI Assistance

| Area                   | My involvement                      | Claude's involvement              |                                     |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------------|
| Overall architecture   | Designed by me                      | Explained/reviewed concepts                 |                                     |
| Phase planning         | Followed four FlyRank phases        | Broke phases into beginner-friendly stages                   |                                     |
| API routes             | Built entirely by me                | No direct implementation           |                                     |
| Service layer          | Built entirely by me                | Debugging/explanation when needed                   |                                     |
| Repository layer       | Built entirely by me                | No direct implementation           |                                     |
| Data model             | Designed by me                      | Helped explain/document                 |                                     |
| Supabase integration   | Mixed                               | Explained tenant-ID approach and assisted with portions of code    |                                     |
| Geo enrichment         | Mixed                               | Helped implement/correct code and explain fallback                 |                                     |
| Rate limiting          | Implemented by me                   | Explained approach and helped debug testing                  |                                     |
| Honeypot               | Wired into project by me            | Explained approach and provided implementation code      |                                     |
| CORS                   | Implemented/integrated by me        | Significant debugging assistance               |                                     |
| Widget delivery        | Implemented by me                   | Guidance/debugging where required                 |                                     |
| Dashboard API          | Implemented by me                   | Guidance/debugging where required                 |                                     |
| Tests                  | Written/run by me                   | Helped debug failures and identify issues                   |                                     |
| Additional basic tests | Added by me                         | Initial AI guidance missed some                     |                                     |
| Dockerfile             | Built by me                         | Minor debugging assistance only                     |                                     |
| docker-compose.yml     | Built by me                         | Minor debugging assistance only                     |                                     |
| README.md              | Final version reviewed/edited by me | Generated initial documentation            |                                     |
| DESIGN.md              | Final version reviewed/edited by me | Generated initial documentation            |                                     |
| capstone.yaml          | Final version reviewed/edited by me | Generated initial documentation            |                                     |
| EVIDENCE.md            | Built entirely by me                | No document generation               |                                     |
| Debugging              | Performed by me                     | Explained errors and suggested fixes                    |                                     |

---

# 11. AI Usage Philosophy

I used Claude as a development assistant rather than treating it as a replacement for understanding the project.

The most useful part of the AI assistance was not simply receiving code. For the unfamiliar parts of the project, I first used Claude's guides to understand:

* what the component was supposed to accomplish
* why it was needed
* how it interacted with the rest of the system
* what failure cases needed to be handled
* how to test the behavior

For selected components, Claude generated portions of code that I then wired into the application. I made sure I understood those portions before relying on them.

For debugging, I generally supplied the actual error output or screenshots rather than asking Claude to arbitrarily rewrite working code. This allowed the debugging process to be based on the observed behavior.

I also reviewed Claude's suggestions instead of assuming they were complete or automatically correct. One concrete example was the test plan: the initial AI guidance covered the more technically significant cases but missed some general tests, which I identified and added myself.

---

# 12. Final Ownership

The final application is my implementation.

I made the architecture and major design decisions, implemented the API routes, service layer, repository layer, Docker configuration, testing workflow, and evidence collection. I also reviewed and edited the AI-assisted documentation.

Claude contributed through phase-by-phase guidance, explanations, selected code generation, and debugging assistance.

The purpose of recording this distinction is not to claim that AI was never used. AI was used throughout the project where it was useful. The important distinction is that I used it to understand, implement, debug, and improve the system rather than treating generated code as a black box.

The final system reflects the architecture and scope defined for the capstone: authenticated widget management, public cached delivery, cross-origin submissions, validation, rate limiting, honeypot spam protection, geo-enrichment fallback, persistence, safe notification behavior, and dashboard access to submissions and statistics.
