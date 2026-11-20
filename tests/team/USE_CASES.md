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

- **Assigned contributor:** `@Artfever` (author review/commit pending)
- **Links:** FR-B01–FR-B06; BR-C01–BR-C03; risks PR-01, PR-02, PR-03
- **Actor:** Librarian
- **Preconditions:** Student and available newspaper exist; actor has staff role; valid session and CSRF token.
- **Main flow:** 1) Select student and newspaper. 2) Submit exactly one `newspaperId` with required student and borrow date. 3) System creates the loan and marks the newspaper unavailable. 4) API responds `201`.
- **Alternate flows:** A1) Omit due date and verify the 14-day default. A2) Supply a due date and verify exact persistence.
- **Exception flows:** E1) Newspaper is unavailable: request fails with no new record. E2) Newspaper ID does not exist: not-found response and no state change.
- **Postconditions:** One active record references the newspaper; it is unavailable; snapshot and dates are persisted.

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

- **Assigned contributor:** `@TahaSohail-Goat` (author review/commit pending)
- **Links:** FR-R01–FR-R06; BR-C04; risks PR-04, PR-05, PR-06
- **Actor:** Librarian
- **Preconditions:** Active record references an unavailable newspaper; actor has staff role and valid CSRF token.
- **Main flow:** 1) Submit return for the active record. 2) System writes today's return date and sets newspaper available. 3) API responds `204`.
- **Alternate flows:** A1) Administrator performs the same transition. A2) Student reads their own history and sees the returned record, but cannot mutate it.
- **Exception flows:** E1) Record is already returned: `ALREADY_RETURNED`, original return date and state unchanged. E2) Invalid/missing record ID: not-found, no state change.
- **Postconditions:** Newspaper is available; one returned record is retained; repeat return does not create another transition or row.

