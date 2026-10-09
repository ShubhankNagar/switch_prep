package com.switchprep.quiz;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QuizAttemptRepository extends JpaRepository<QuizAttempt, Long> {

    List<QuizAttempt> findByUserIdOrderByTakenAtDesc(Long userId);

    void deleteByUserId(Long userId);
}
