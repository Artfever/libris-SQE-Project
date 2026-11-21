package com.example.lms.team;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import com.example.lms.dto.*;
import com.example.lms.entity.*;
import com.example.lms.event.EntityAuditEvent;
import com.example.lms.exception.*;
import com.example.lms.repository.*;
import com.example.lms.service.BorrowRecordService;
import com.example.lms.util.CurrentUser;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.stream.IntStream;
import java.util.stream.Stream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.*;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class TeamCirculationTest {
  enum Kind {
    BOOK,
    MAGAZINE,
    NEWSPAPER
  }

  private static final LocalDate BORROWED = LocalDate.of(2026, 2, 25);
  private static final long ITEM = 11L;
  private static final long STUDENT = 22L;
  private static final long LOAN = 33L;
  private static final Pageable PAGE = PageRequest.of(0, 10);

  @Mock BorrowRecordRepository records;
  @Mock BookRepository books;
  @Mock MagazineRepository magazines;
  @Mock NewspaperRepository newspapers;
  @Mock StudentProfileRepository students;
  @Mock ApplicationEventPublisher events;
  @Mock CurrentUser currentUser;

  private BorrowRecordService service;
  private StudentProfile student;
  private Book book;
  private Magazine magazine;
  private Newspaper newspaper;

  @BeforeEach
  void setup() {
    service =
        new BorrowRecordService(
            records, books, magazines, newspapers, students, events, currentUser);
    student = new StudentProfile();
    book = new Book();
    magazine = new Magazine();
    newspaper = new Newspaper();
    ReflectionTestUtils.setField(student, "id", STUDENT);
    for (var item : List.of(book, magazine, newspaper)) {
      ReflectionTestUtils.setField(item, "id", ITEM);
    }
    student.setName("Synthetic Borrower");
    student.setEmail("borrower@example.invalid");
    student.setPhone("03000000001");
    book.setTitle("Book");
    magazine.setTitle("Magazine");
    newspaper.setTitle("Newspaper");
  }

  static Stream<Integer> selections() {
    return IntStream.range(0, 8).boxed();
  }

  @ParameterizedTest
  @MethodSource("selections")
  void itemSelectionMcc(int mask) {
    if (Integer.bitCount(mask) != 1) {
      var error =
          assertThrows(BusinessRuleException.class, () -> service.borrow(request(mask, null)));
      assertEquals("INVALID_REQUEST", error.getCode());
      verifyNoInteractions(students, records, books, magazines, newspapers, events);
      return;
    }
    var kind = Kind.values()[Integer.numberOfTrailingZeros(mask)];
    var due = kind == Kind.MAGAZINE ? BORROWED.plusDays(2) : null;
    when(students.findById(STUDENT)).thenReturn(Optional.of(student));
    itemLookup(kind, true, true);
    actor();
    when(records.save(any()))
        .thenAnswer(
            call -> {
              BorrowRecord saved = call.getArgument(0);
              ReflectionTestUtils.setField(saved, "id", LOAN);
              assertSame(student, saved.getStudent());
              return saved;
            });

    var loan = service.borrow(request(mask, due));
    assertEquals(LOAN, loan.id());
    assertEquals(ITEM, loan.itemId());
    assertEquals(kind.name(), loan.itemType());
    assertEquals("BORROWED", loan.status());
    assertNull(loan.returnDate());
    assertEquals(STUDENT, loan.studentId());
    assertEquals(student.getName(), loan.borrowerName());
    assertEquals(student.getEmail(), loan.borrowerEmail());
    assertEquals(student.getPhone(), loan.borrowerPhone());
    assertEquals(BORROWED, loan.borrowDate());
    assertEquals(due == null ? BORROWED.plusDays(14) : due, loan.dueDate());
    assertFalse(available(kind));
    verify(records).save(any());
    verify(events).publishEvent(any(EntityAuditEvent.class));
  }

  @ParameterizedTest
  @EnumSource(Kind.class)
  void missingItemStopsBorrow(Kind kind) {
    when(students.findById(STUDENT)).thenReturn(Optional.of(student));
    itemLookup(kind, false, false);
    assertThrows(
        ResourceNotFoundException.class, () -> service.borrow(request(1 << kind.ordinal(), null)));
    verifyNoInteractions(records, events);
  }

  @ParameterizedTest
  @EnumSource(Kind.class)
  void unavailableItemStopsBorrow(Kind kind) {
    when(students.findById(STUDENT)).thenReturn(Optional.of(student));
    itemLookup(kind, true, false);
    var error =
        assertThrows(
            BusinessRuleException.class, () -> service.borrow(request(1 << kind.ordinal(), null)));
    assertEquals("UNAVAILABLE", error.getCode());
    assertFalse(available(kind));
    verifyNoInteractions(records, events);
  }

  @Test
  void missingStudentStopsBorrowBeforeItemLookup() {
    when(students.findById(STUDENT)).thenReturn(Optional.empty());
    assertThrows(ResourceNotFoundException.class, () -> service.borrow(request(1, null)));
    verifyNoInteractions(records, books, magazines, newspapers, events);
  }

  @ParameterizedTest
  @EnumSource(Kind.class)
  void firstReturnRestoresItemAndRepeatPreservesDate(Kind kind) {
    var record = loan(kind);
    when(records.findByIdForReturn(LOAN)).thenReturn(Optional.of(record));
    itemLookup(kind, true, false);
    actor();
    var today = LocalDate.now();
    service.returnBook(LOAN);
    assertTrue(available(kind));
    assertTrue(List.of(today, LocalDate.now()).contains(record.getReturnDate()));
    var returned = record.getReturnDate();
    var error = assertThrows(BusinessRuleException.class, () -> service.returnBook(LOAN));
    assertEquals("ALREADY_RETURNED", error.getCode());
    assertEquals(returned, record.getReturnDate());
    verify(events).publishEvent(any(EntityAuditEvent.class));
  }

  @ParameterizedTest
  @EnumSource(Kind.class)
  void missingReferencedItemStopsReturnBeforeAudit(Kind kind) {
    when(records.findByIdForReturn(LOAN)).thenReturn(Optional.of(loan(kind)));
    itemLookup(kind, false, false);
    assertThrows(ResourceNotFoundException.class, () -> service.returnBook(LOAN));
    verifyNoInteractions(events);
  }

  @Test
  void rejectsMissingLoan() {
    when(records.findByIdForReturn(LOAN)).thenReturn(Optional.empty());
    assertThrows(ResourceNotFoundException.class, () -> service.returnBook(LOAN));
    verifyNoInteractions(books, magazines, newspapers, events);
  }

  @Test
  void retainedHistorySupportsDeletedItem() {
    var orphan = loan(null);
    when(records.findByIdForReturn(LOAN)).thenReturn(Optional.of(orphan));
    when(records.findAll(PAGE)).thenReturn(new PageImpl<>(List.of(orphan)));
    actor();
    service.returnBook(LOAN);
    var row = service.list(null, null, PAGE).getContent().getFirst();
    assertEquals("RETURNED", row.status());
    assertNull(row.itemId());
    assertNotNull(row.returnDate());
    verifyNoInteractions(books, magazines, newspapers);
    verify(events).publishEvent(any(EntityAuditEvent.class));
  }

  @Test
  void routesStaffHistorySearchAndFilters() {
    when(records.search("borrower", PAGE)).thenReturn(new PageImpl<>(List.of(loan(Kind.BOOK))));
    assertEquals(ITEM, service.list("RETURNED", "borrower", PAGE).getContent().getFirst().itemId());
    when(records.findByReturnDateIsNull(PAGE)).thenReturn(Page.empty());
    when(records.findByReturnDateIsNotNull(PAGE)).thenReturn(Page.empty());
    when(records.findAll(PAGE)).thenReturn(Page.empty());
    service.list("borrowed", " ", PAGE);
    service.list("returned", null, PAGE);
    service.list("other", null, PAGE);
  }

  @Test
  void resolvesStudentBeforeReadingScopedHistory() {
    when(students.findByAccountUsername("synthetic")).thenReturn(Optional.of(student));
    when(records.findByStudentIdAndReturnDateIsNull(STUDENT, PAGE)).thenReturn(Page.empty());
    when(records.findByStudentIdAndReturnDateIsNotNull(STUDENT, PAGE)).thenReturn(Page.empty());
    when(records.findByStudentId(STUDENT, PAGE)).thenReturn(Page.empty());
    service.listByCurrentStudent("synthetic", "BORROWED", PAGE);
    service.listByCurrentStudent("synthetic", "RETURNED", PAGE);
    service.listByCurrentStudent("synthetic", null, PAGE);
    assertThrows(
        ResourceNotFoundException.class, () -> service.listByCurrentStudent("unknown", null, PAGE));
  }

  private BorrowRequest request(int mask, LocalDate due) {
    return new BorrowRequest(
        (mask & 1) == 0 ? null : ITEM,
        (mask & 2) == 0 ? null : ITEM,
        (mask & 4) == 0 ? null : ITEM,
        STUDENT,
        "ignored",
        "ignored",
        "ignored",
        BORROWED,
        due);
  }

  private void itemLookup(Kind kind, boolean exists, boolean available) {
    switch (kind) {
      case BOOK -> {
        book.setAvailable(available);
        when(books.findByIdForBorrow(ITEM))
            .thenReturn(exists ? Optional.of(book) : Optional.empty());
      }
      case MAGAZINE -> {
        magazine.setAvailable(available);
        when(magazines.findByIdForBorrow(ITEM))
            .thenReturn(exists ? Optional.of(magazine) : Optional.empty());
      }
      case NEWSPAPER -> {
        newspaper.setAvailable(available);
        when(newspapers.findByIdForBorrow(ITEM))
            .thenReturn(exists ? Optional.of(newspaper) : Optional.empty());
      }
    }
  }

  private boolean available(Kind kind) {
    return switch (kind) {
      case BOOK -> book.isAvailable();
      case MAGAZINE -> magazine.isAvailable();
      case NEWSPAPER -> newspaper.isAvailable();
    };
  }

  private BorrowRecord loan(Kind kind) {
    var record = new BorrowRecord();
    ReflectionTestUtils.setField(record, "id", LOAN);
    record.setStudent(student);
    record.setBorrowDate(BORROWED);
    record.setBook(kind == Kind.BOOK ? book : null);
    record.setMagazine(kind == Kind.MAGAZINE ? magazine : null);
    record.setNewspaper(kind == Kind.NEWSPAPER ? newspaper : null);
    return record;
  }

  private void actor() {
    when(currentUser.get())
        .thenReturn(new CurrentUser.Actor(1L, "staff", "LIBRARIAN", "127.0.0.1", "unit-test"));
  }
}
