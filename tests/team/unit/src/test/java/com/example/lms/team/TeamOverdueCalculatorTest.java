package com.example.lms.team;

import static org.junit.jupiter.api.Assertions.*;

import com.example.lms.entity.BorrowRecord;
import com.example.lms.util.OverdueCalculator;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class TeamOverdueCalculatorTest {
  @Test
  void absentRecordOrDatesAreNotOverdue() {
    for (BorrowRecord record : new BorrowRecord[] {null, new BorrowRecord()}) {
      assertNull(OverdueCalculator.effectiveDueDate(record));
      assertFalse(OverdueCalculator.isOverdue(record));
      assertEquals(0, OverdueCalculator.daysOverdue(record));
    }
  }

  @ParameterizedTest
  @ValueSource(ints = {-1, 0, 1})
  void returnedLoanUsesDateOfReturnAtBoundary(int offset) {
    var record = new BorrowRecord();
    record.setBorrowDate(LocalDate.of(2026, 2, 25));
    var due = LocalDate.of(2026, 3, 11);
    record.setReturnDate(due.plusDays(offset));
    assertEquals(due, OverdueCalculator.effectiveDueDate(record));
    assertEquals(offset > 0, OverdueCalculator.isOverdue(record));
    assertEquals(Math.max(0, offset), OverdueCalculator.daysOverdue(record));
  }

  @Test
  void activeLoanUsesTodayAndExplicitDate() {
    var record = new BorrowRecord();
    record.setBorrowDate(LocalDate.now().minusDays(30));
    record.setDueDate(LocalDate.now().plusDays(2));
    assertEquals(record.getDueDate(), OverdueCalculator.effectiveDueDate(record));
    assertFalse(OverdueCalculator.isOverdue(record));
    assertEquals(0, OverdueCalculator.daysOverdue(record));
  }
}
