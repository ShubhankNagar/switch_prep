package com.switchprep.habit;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.Instant;
import java.time.LocalDate;

/** One day of the routine: manually entered habit values, study minutes and a one-line journal. */
@Entity
@Table(name = "habit_log", uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "log_date"}))
public class HabitLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "log_date", nullable = false)
    private LocalDate logDate;

    /** JSON object of habitId -> number for manual habits (auto habits are derived from progress). */
    @Column(columnDefinition = "TEXT")
    private String valuesJson;

    private int minutes;

    @Column(length = 1000)
    private String journal;

    @Column(nullable = false)
    private Instant updatedAt = Instant.now();

    protected HabitLog() {
    }

    public HabitLog(Long userId, LocalDate logDate) {
        this.userId = userId;
        this.logDate = logDate;
    }

    public LocalDate getLogDate() { return logDate; }
    public String getValuesJson() { return valuesJson; }
    public void setValuesJson(String valuesJson) { this.valuesJson = valuesJson; }
    public int getMinutes() { return minutes; }
    public void setMinutes(int minutes) { this.minutes = minutes; }
    public String getJournal() { return journal; }
    public void setJournal(String journal) { this.journal = journal; }
    public Instant getUpdatedAt() { return updatedAt; }
    public void touch() { this.updatedAt = Instant.now(); }
}
