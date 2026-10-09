package com.switchprep.progress;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public final class ProgressDtos {

    private ProgressDtos() {
    }

    public record ProgressItem(String key, String section, boolean done, boolean revise, String note,
                               Instant completedAt, Instant updatedAt) {
        static ProgressItem from(ItemProgress p) {
            return new ProgressItem(p.getItemKey(), p.getSection(), p.isDone(), p.isRevise(), p.getNote(),
                    p.getCompletedAt(), p.getUpdatedAt());
        }
    }

    /** Partial update: null fields are left unchanged. */
    public record ProgressUpdate(@NotBlank @Size(max = 30) String section, Boolean done, Boolean revise,
                                 @Size(max = 20000) String note) {
    }
}
