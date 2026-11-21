package com.example.lms.team;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import com.example.lms.dto.BorrowRequest;
import com.example.lms.entity.*;
import com.example.lms.repository.*;
import com.example.lms.service.AuditService;
import com.example.lms.service.BorrowRecordService;
import com.example.lms.util.CurrentUser;
import java.time.LocalDate;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(
    properties = {
      "spring.datasource.url=jdbc:h2:mem:team-recovery;MODE=MySQL;DB_CLOSE_DELAY=-1",
      "spring.jpa.hibernate.ddl-auto=create-drop",
      "spring.flyway.enabled=false"
    })
class TeamRecoveryTest {
  @Autowired BorrowRecordService service;
  @Autowired BorrowRecordRepository records;
  @Autowired BookRepository books;
  @Autowired StudentProfileRepository students;
  @Autowired AccountRepository accounts;
  @MockitoBean AuditService audit;
  @MockitoBean CurrentUser currentUser;

  private Long bookId;
  private Long studentId;

  @BeforeEach
  void fixture() {
    var account = new Account();
    account.setUsername("recovery-student");
    account.setPasswordHash("synthetic-unused-hash");
    account.setRole(Role.STUDENT);
    account = accounts.save(account);
    var student = new StudentProfile();
    student.setAccount(account);
    student.setName("Recovery Student");
    student.setEmail("recovery@example.invalid");
    student.setPhone("03000000001");
    studentId = students.save(student).getId();
    var book = new Book();
    book.setTitle("Recovery Book");
    book.setIsbn("9780000000901");
    book.setAvailable(true);
    bookId = books.save(book).getId();
    when(currentUser.get())
        .thenReturn(new CurrentUser.Actor(1L, "synthetic-admin", "ADMIN", "127.0.0.1", "recovery-test"));
  }

  @AfterEach
  void cleanup() {
    records.deleteAll();
    books.deleteAll();
    students.deleteAll();
    accounts.deleteAll();
  }

  @Test
  void auditDependencyFailureRollsBackThenRetryCreatesOneLoan() {
    var request =
        new BorrowRequest(bookId, null, null, studentId, null, null, null, LocalDate.now(), null);
    doThrow(new IllegalStateException("synthetic audit outage"))
        .when(audit)
        .log(any(), any(), any(), any(), any(), any(), any(), any(), any(), any());

    assertThrows(IllegalStateException.class, () -> service.borrow(request));
    assertTrue(books.findById(bookId).orElseThrow().isAvailable(), "rollback must restore availability");
    assertEquals(0, records.count(), "rollback must leave no loan history");

    reset(audit);
    var loan = service.borrow(request);
    assertEquals("BORROWED", loan.status());
    assertFalse(books.findById(bookId).orElseThrow().isAvailable());
    assertEquals(1, records.count());

    service.returnBook(loan.id());
    assertTrue(books.findById(bookId).orElseThrow().isAvailable());
    assertNotNull(records.findById(loan.id()).orElseThrow().getReturnDate());
    assertEquals(1, records.count(), "recovery must not duplicate loan history");
  }
}
