# Circulation test basis

**Scope:** borrowing and returning books, magazines, and newspapers in Libris.
**Source baseline:** the checked-in application at the commit linked from the
associated Phase 2 pull request. These requirements describe current source
behavior; they do not add unstated business policy.

## Functional requirements

| ID | Requirement | Workflow | Source / verification |
| --- | --- | --- | --- |
| FR-B01 | An authenticated `ADMIN` or `LIBRARIAN` can create a borrow record for exactly one book, magazine, or newspaper and a real student. | Borrow | `BorrowRecordService.borrow`; `SecurityConfig`; API test |
| FR-B02 | A borrow request must contain `studentId` and `borrowDate`; missing either is rejected by request validation. | Borrow | `BorrowRequest`; `@Valid` controller; API test |
| FR-B03 | A borrow request with zero or multiple item IDs is rejected and does not change availability or create history. | Borrow | `BorrowRecordService.borrow`; FR-B01 |
| FR-B04 | A selected item must exist and be available; a successful borrow marks it unavailable and persists one active record. | Borrow | `BorrowRecordService.borrow`; item repositories; read-back test |
| FR-B05 | If no due date is supplied, the record uses `borrowDate + 14 days`; an explicitly supplied due date is stored as supplied. | Borrow | `BorrowRecordService.borrow`; date boundary tests |
| FR-B06 | A successful borrow stores a borrower name, email, and phone snapshot from the student profile and retains it in the borrow record. | Borrow | `BorrowRecordService.borrow`; `BorrowRecord`; read-back test |
| FR-R01 | An authenticated `ADMIN` or `LIBRARIAN` can return an existing active borrow record; success sets its return date to the server's current local date and makes its referenced item available. | Return | `SecurityConfig`; `BorrowRecordService.returnBook`; read-back test |
| FR-R02 | Returning an already returned record is rejected; the original return date and item/history state remain unchanged. | Return | `BorrowRecordService.returnBook`; repeat-request test |
| FR-R03 | A return request for a missing record is rejected and changes no catalogue availability or history. | Return | `BorrowRecordService.returnBook`; not-found API test |
| FR-R04 | A `STUDENT` may read their own borrow history but cannot create or return records. | Both | `SecurityConfig`; `/api/borrow-records/my`; role tests |
| FR-R05 | Borrow and return history remains listable after item availability changes, including the returned record and its dates. | Both | `BorrowRecordService.list*`; `BorrowRecord`; history read-back test |
| FR-R06 | Unsafe browser requests must include the session and CSRF token; requests failing either authentication/authorization or CSRF checks are rejected without state changes. | Both | `SecurityConfig`; `SpaCsrfTokenRequestHandler`; CSRF integration test |

## Business rules

| ID | Rule | Evidence / status |
| --- | --- | --- |
| BR-C01 | **Single-item boundary:** among `bookId`, `magazineId`, and `newspaperId`, exactly one must be non-null. Zero and two-or-more are rejected. | Implemented in `BorrowRecordService.borrow`; no request DTO constraint expresses it. |
| BR-C02 | **Availability decision:** a borrow succeeds only when the selected item exists **and** its availability flag is true. Missing item yields not-found; existing unavailable item yields `UNAVAILABLE`. | Implemented for each type in `BorrowRecordService.borrow`. |
| BR-C03 | **Borrow transition:** successful borrow atomically changes available → unavailable and creates one active borrow record with a student snapshot. Rejected requests preserve both states. | Service transaction, pessimistic item lookup, and persistence; verify state after success and rejection. |
| BR-C04 | **Return transition:** an active record changes to returned with `returnDate = LocalDate.now()` and its item changes unavailable → available; a record already returned cannot transition again. | Implemented in `BorrowRecordService.returnBook`; repeated return produces `ALREADY_RETURNED`. |
| BR-C05 | **Due-date default:** due date defaults to borrow date plus 14 days only when omitted. The source currently does not reject a supplied due date earlier than the borrow date or a borrow date in the future; treat those as unspecified policy, not defects, unless the owner changes the rule. | Implemented in `BorrowRecordService.borrow`; no ordering validation appears on `BorrowRequest`. |

## HTTP and error contract notes

- Borrow: `POST /api/borrow-records`; success is `201 Created` with a response body and `Location` for the new record.
- Return: `POST /api/borrow-records/{id}/return`; success is `204 No Content`.
- Role rules: staff can list/create/return; students can read `/api/borrow-records/my`. Check the live `SecurityConfig` when adding cases.
- Validation, business-rule, not-found, unauthorized, forbidden, and CSRF failures use the application's configured error handling. Tests should assert stable status/error codes and state, not incidental message wording.
- Return dates use the app server's `LocalDate.now()`; tests must control or bound the date assertion rather than assume a timezone-independent instant.

