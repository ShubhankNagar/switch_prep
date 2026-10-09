package com.switchprep.habit;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

/**
 * A user's habit definitions (the daily routine), stored as a JSON array. The frontend owns the shape
 * (see HabitDef in frontend/src/app/core/models.ts); the API stores it opaquely so routines can evolve freely.
 */
@Entity
@Table(name = "habit_settings")
public class HabitSettings {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String habitsJson;

    @Column(nullable = false)
    private Instant updatedAt = Instant.now();

    protected HabitSettings() {
    }

    public HabitSettings(Long userId, String habitsJson) {
        this.userId = userId;
        this.habitsJson = habitsJson;
    }

    public String getHabitsJson() { return habitsJson; }
    public Instant getUpdatedAt() { return updatedAt; }

    public void setHabitsJson(String habitsJson) {
        this.habitsJson = habitsJson;
        this.updatedAt = Instant.now();
    }
}
