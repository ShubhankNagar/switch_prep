package com.switchprep.habit;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HabitLogRepository extends JpaRepository<HabitLog, Long> {

    Optional<HabitLog> findByUserIdAndLogDate(Long userId, LocalDate logDate);

    List<HabitLog> findByUserIdAndLogDateBetweenOrderByLogDateAsc(Long userId, LocalDate from, LocalDate to);

    List<HabitLog> findByUserIdOrderByLogDateAsc(Long userId);

    void deleteByUserId(Long userId);
}
