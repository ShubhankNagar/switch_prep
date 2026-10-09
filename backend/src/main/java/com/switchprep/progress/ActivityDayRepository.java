package com.switchprep.progress;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityDayRepository extends JpaRepository<ActivityDay, Long> {

    Optional<ActivityDay> findByUserIdAndDay(Long userId, LocalDate day);

    List<ActivityDay> findByUserIdOrderByDayAsc(Long userId);

    void deleteByUserId(Long userId);
}
