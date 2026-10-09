package com.switchprep.quiz;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.Instant;

/** One attempt at an MCQ set, e.g. quizKey "final:d3" or "ai:m04-ml-basics-02". */
@Entity
@Table(name = "quiz_attempt", indexes = @Index(columnList = "user_id,quiz_key"))
public class QuizAttempt {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "quiz_key", nullable = false, length = 150)
    private String quizKey;

    private int score;

    private int total;

    /** JSON map of questionId -> chosen option index. */
    @Column(columnDefinition = "TEXT")
    private String answersJson;

    private int durationSeconds;

    @Column(nullable = false)
    private Instant takenAt = Instant.now();

    protected QuizAttempt() {
    }

    public QuizAttempt(Long userId, String quizKey, int score, int total, String answersJson, int durationSeconds) {
        this.userId = userId;
        this.quizKey = quizKey;
        this.score = score;
        this.total = total;
        this.answersJson = answersJson;
        this.durationSeconds = durationSeconds;
    }

    public Long getId() { return id; }
    public String getQuizKey() { return quizKey; }
    public int getScore() { return score; }
    public int getTotal() { return total; }
    public String getAnswersJson() { return answersJson; }
    public int getDurationSeconds() { return durationSeconds; }
    public Instant getTakenAt() { return takenAt; }
    public void setTakenAt(Instant takenAt) { this.takenAt = takenAt; }
}
