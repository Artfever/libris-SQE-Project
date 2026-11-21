# Circulation use cases

These six use-case specifications are the phase lead's integrated drafts, based
on current circulation source. “Assigned contributor” identifies the teammate
expected to review, revise, and claim authorship through an identifiable commit;
it is not a claim that the teammate wrote this draft. The Phase 2 #9 acceptance
condition for individual authorship remains open until those contributions
land.

Common conventions: staff actor means `ADMIN` or `LIBRARIAN`; requests are
same-origin and authenticated with a valid CSRF token. Postconditions refer to
persisted database state, not only the HTTP response.

## UC-01 — Borrow an available book

- **Assigned contributor:** `@Artfever` (author review/commit pending)
- **Links:** FR-B01–FR-B06; BR-C01–BR-C03; risks PR-01, PR-02, PR-03
- **Actor:** Librarian
- **Preconditions:** Student exists; book exists and is available; actor has a staff role; CSRF token is current.
- **Main flow:** 1) Open borrow workflow. 2) Select one student and book. 3) Submit `studentId`, `bookId`, `borrowDate`, and borrower fields as expected by the API. 4) System validates and locks the item, creates the record, marks the book unavailable, and responds `201`.
- **Alternate flows:** A1) Omit `dueDate`; system stores borrow date plus 14 days. A2) Supply a due date; system stores that supplied date.
- **Exception flows:** E1) Book is unavailable; request fails and no additional record is created. E2) Student or book ID does not exist; request fails and availability/history remain unchanged.
- **Postconditions:** Exactly one active record references the book and student, borrower contact values are snapshotted, book availability is false.

## UC-02 — Borrow an available magazine

- **Assigned contributor:** `@Artfever` (author review/commit pending)
- **Links:** FR-B01–FR-B06; BR-C01–BR-C03; risks PR-01, PR-02, PR-03
- **Actor:** Administrator
- **Preconditions:** Student and available magazine exist; actor has staff role; valid session and CSRF token.
- **Main flow:** 1) Select student and magazine. 2) Submit one `magazineId` and required student/borrow date. 3) System checks availability and persists the loan. 4) API responds `201`.
- **Alternate flows:** A1) Omit due date and verify the 14-day default. A2) Supply an explicit due date and verify it is preserved.
- **Exception flows:** E1) Magazine already unavailable: error, no new record. E2) Magazine ID is missing from the catalogue: not-found response, no state change.
- **Postconditions:** One active record references the magazine; its availability is false; student snapshot is retained.

## UC-03 — Borrow an available newspaper

- **Assigned contributor:** `@Abdullah-SE-bit` (24I-3020)
- **Links:** FR-B01–FR-B06; BR-C01–BR-C03; risks PR-01, PR-02, PR-03
- **Actor:** Librarian
- **Preconditions:** The student and newspaper exist; the newspaper is available; the caller is authenticated as `LIBRARIAN`; a current CSRF token is present.
- **Main flow:** 1) The librarian selects a student and available newspaper. 2) The client sends `POST /api/borrow-records` with `studentId`, `newspaperId`, and `borrowDate` (and optional borrower fields). 3) The service validates the single-item selection, locks and checks the newspaper, snapshots the student's contact values, creates one active record, and marks the newspaper unavailable in the same transaction. 4) The API responds `201` with the created record.
- **Alternate flows:** A1) `dueDate` is omitted; the record stores `borrowDate + 14 days`. A2) An explicit `dueDate` is supplied; that date is persisted unchanged.
- **Exception flows:** E1) The newspaper exists but is unavailable; the request is rejected and neither a new active record nor another availability change is persisted. E2) The newspaper ID does not exist; the request is rejected as not found and the student history and catalogue state remain unchanged.
- **Postconditions:** Exactly one active record references the selected student and newspaper; the newspaper is unavailable; borrower snapshot, borrow date, and effective due date are persisted. A rejected request leaves those state values unchanged.

## UC-04 — Return a borrowed book

- **Assigned contributor:** `@TahaSohail-Goat` (author review/commit pending)
- **Links:** FR-R01–FR-R06; BR-C04; risks PR-04, PR-05, PR-06
- **Actor:** Librarian
- **Preconditions:** An active record references a book currently marked unavailable; actor has staff role; valid session and CSRF token.
- **Main flow:** 1) Submit `POST /api/borrow-records/{id}/return`. 2) System locks the record, sets its return date to today, and restores book availability. 3) API responds `204`.
- **Alternate flows:** A1) Return from an administrator account; same persisted transition. A2) Read the record list after return and verify it appears as returned with its original borrower snapshot and dates.
- **Exception flows:** E1) Record ID does not exist: not-found response, no catalogue change. E2) A student attempts the mutation: `403` (or current configured forbidden response), no state change.
- **Postconditions:** Record remains in history with non-null return date; book is available; no duplicate history row is created.

## UC-05 — Return a borrowed magazine

- **Assigned contributor:** `@TahaSohail-Goat` (author review/commit pending)
- **Links:** FR-R01–FR-R06; BR-C04; risks PR-04, PR-05, PR-06
- **Actor:** Administrator
- **Preconditions:** Active borrow record references an unavailable magazine; staff session and valid CSRF token.
- **Main flow:** 1) Submit return for the record ID. 2) System dates the return and restores magazine availability. 3) API returns `204`.
- **Alternate flows:** A1) Librarian performs the same return. A2) Read the returned record and magazine after the operation; history is retained and status is returned.
- **Exception flows:** E1) Missing record ID: not-found with no state change. E2) Student attempts return: forbidden with no state change.
- **Postconditions:** Magazine is available; record has return date and stays in history.

## UC-06 — Return a borrowed newspaper

- **Assigned contributor:** `@Abdullah-SE-bit` (24I-3020)
- **Links:** FR-R01–FR-R06; BR-C04; risks PR-04, PR-05, PR-06
- **Actor:** Librarian
- **Preconditions:** An active borrow record references a newspaper currently marked unavailable; the caller is authenticated as `LIBRARIAN`; a current CSRF token is present.
- **Main flow:** 1) The librarian submits `POST /api/borrow-records/{id}/return` for the active record. 2) The service locks the record, sets `returnDate` to the current local date, marks the referenced newspaper available, and commits the transition atomically. 3) The API responds `204`.
- **Alternate flows:** A1) An authenticated `ADMIN` submits the same request and receives the same persisted transition. A2) The student reads `/api/borrow-records/my` after the return and sees the returned record and its original borrow details, while remaining unable to perform the mutation.
- **Exception flows:** E1) The record is already returned; the request is rejected with `ALREADY_RETURNED`, preserving its original return date and catalogue state. E2) The record ID is absent from the database; the request is rejected as not found and no catalogue or history state changes.
- **Postconditions:** The record remains in history with a non-null return date and the newspaper is available. A repeated return creates no row and does not change the original return date.

