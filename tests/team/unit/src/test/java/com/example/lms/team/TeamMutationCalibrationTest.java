package com.example.lms.team;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.example.lms.dto.BorrowRequest;
import com.example.lms.entity.*;
import com.example.lms.repository.*;
import com.example.lms.service.BorrowRecordService;
import com.example.lms.util.CurrentUser;
import java.time.LocalDate;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.test.util.ReflectionTestUtils;

/** Intentionally weak smoke test used only to calibrate survivor analysis. */
@ExtendWith(MockitoExtension.class)
class TeamMutationCalibrationTest {
  @Mock BorrowRecordRepository records;
  @Mock BookRepository books;
  @Mock MagazineRepository magazines;
  @Mock NewspaperRepository newspapers;
  @Mock StudentProfileRepository students;
  @Mock ApplicationEventPublisher events;
  @Mock CurrentUser currentUser;

  @Test
  void minimalBorrowSmoke() {
    var student = new StudentProfile();
    ReflectionTestUtils.setField(student, "id", 1L);
    student.setName("Synthetic Student");
    student.setEmail("student@example.invalid");
    student.setPhone("03000000001");
    var book = new Book();
    ReflectionTestUtils.setField(book, "id", 2L);
    book.setTitle("Synthetic Book");
    book.setAvailable(true);
    when(students.findById(1L)).thenReturn(Optional.of(student));
    when(books.findByIdForBorrow(2L)).thenReturn(Optional.of(book));
    when(records.save(any(BorrowRecord.class)))
        .thenAnswer(
            invocation -> {
              var record = invocation.getArgument(0, BorrowRecord.class);
              ReflectionTestUtils.setField(record, "id", 3L);
              return record;
            });
    when(currentUser.get())
        .thenReturn(new CurrentUser.Actor(4L, "synthetic-admin", "ADMIN", "127.0.0.1", "pit-calibration"));
    var service =
        new BorrowRecordService(records, books, magazines, newspapers, students, events, currentUser);
    var response = service.borrow(
        new BorrowRequest(2L, null, null, 1L, null, null, null, LocalDate.of(2026, 2, 25), null));
    assertNotNull(response);
  }
}
