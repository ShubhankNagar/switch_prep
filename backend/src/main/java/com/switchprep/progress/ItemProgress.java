package com.switchprep.progress;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.Instant;

/**
 * Progress on one piece of content, identified by a key such as "dsa:two-sum",
 * "plan:d12:t3", "core:java-001" or "ai:m08-rag-01". Keys are defined by the frontend content files.
 */
@Entity
@Table(name = "item_progress",
        uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "item_key"}),
        indexes = @Index(columnList = "user_id,section"))
public class ItemProgress {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "item_key", nullable = false, length = 150)
    private String itemKey;

    @Column(nullable = false, length = 30)
    private String section;

    private boolean done;

    /** Flagged for revision ("revise later"). */
    private boolean revise;

    @Column(columnDefinition = "TEXT")
    private String note;

    private Instant completedAt;

    @Column(nullable = false)
    private Instant updatedAt = Instant.now();

    protected ItemProgress() {
    }

    public ItemProgress(Long userId, String itemKey, String section) {
        this.userId = userId;
        this.itemKey = itemKey;
        this.section = section;
    }

    public Long getId() { return id; }
    public Long getUserId() { return userId; }
    public String getItemKey() { return itemKey; }
    public String getSection() { return section; }
    public void setSection(String section) { this.section = section; }
    public boolean isDone() { return done; }
    public boolean isRevise() { return revise; }
    public void setRevise(boolean revise) { this.revise = revise; }
    public String getNote() { return note; }
    public void setNote(String note) { this.note = note; }
    public Instant getCompletedAt() { return completedAt; }
    public void setCompletedAt(Instant completedAt) { this.completedAt = completedAt; }
    public Instant getUpdatedAt() { return updatedAt; }
    public void touch() { this.updatedAt = Instant.now(); }

    public void setDone(boolean done) {
        if (done && !this.done && completedAt == null) {
            completedAt = Instant.now();
        } else if (!done) {
            completedAt = null;
        }
        this.done = done;
    }
}
