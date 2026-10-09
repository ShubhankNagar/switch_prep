package com.switchprep.progress;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDate;

/** Number of things completed by a user on a given day; drives streaks and the activity heatmap. */
@Entity
@Table(name = "activity_day", uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "activity_date"}))
public class ActivityDay {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "activity_date", nullable = false)
    private LocalDate day;

    private int actions;

    protected ActivityDay() {
    }

    public ActivityDay(Long userId, LocalDate day) {
        this.userId = userId;
        this.day = day;
    }

    public LocalDate getDay() { return day; }
    public int getActions() { return actions; }
    public void increment() { actions++; }
}
