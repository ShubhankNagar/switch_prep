package com.switchprep.progress;

import com.switchprep.progress.ProgressDtos.ProgressItem;
import com.switchprep.progress.ProgressDtos.ProgressUpdate;
import com.switchprep.config.AppProperties;
import com.switchprep.habit.HabitLogRepository;
import com.switchprep.quiz.QuizAttemptRepository;
import java.time.LocalDate;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ProgressService {

    // column sizes in ItemProgress and the note size accepted by ProgressUpdate
    private static final int MAX_KEY_LENGTH = 150;
    private static final int MAX_SECTION_LENGTH = 30;
    private static final int MAX_NOTE_LENGTH = 20000;

    private final ItemProgressRepository items;
    private final ActivityDayRepository activity;
    private final QuizAttemptRepository quizAttempts;
    private final HabitLogRepository habitLogs;
    private final AppProperties.Limits limits;

    public ProgressService(ItemProgressRepository items, ActivityDayRepository activity,
                           QuizAttemptRepository quizAttempts, HabitLogRepository habitLogs, AppProperties props) {
        this.items = items;
        this.activity = activity;
        this.quizAttempts = quizAttempts;
        this.habitLogs = habitLogs;
        this.limits = props.limits();
    }

    @Transactional(readOnly = true)
    public List<ProgressItem> list(Long userId) {
        return items.findByUserId(userId).stream().map(ProgressItem::from).toList();
    }

    @Transactional
    public ProgressItem upsert(Long userId, String key, ProgressUpdate update) {
        if (key.length() > MAX_KEY_LENGTH) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Item key is too long");
        }
        ItemProgress p = items.findByUserIdAndItemKey(userId, key).orElseGet(() -> {
            if (items.countByUserId(userId) >= limits.maxProgressItems()) throw limitReached();
            return new ItemProgress(userId, key, update.section());
        });
        boolean wasDone = p.isDone();
        p.setSection(update.section());
        if (update.done() != null) p.setDone(update.done());
        if (update.revise() != null) p.setRevise(update.revise());
        if (update.note() != null) p.setNote(update.note().isBlank() ? null : update.note());
        p.touch();
        ItemProgress saved = items.save(p);
        if (update.note() != null && !update.note().isBlank()) requireNotesWithinLimit(userId);
        if (!wasDone && saved.isDone()) {
            recordActivity(userId);
        }
        return ProgressItem.from(saved);
    }

    @Transactional
    public void delete(Long userId, String key) {
        items.deleteByUserIdAndItemKey(userId, key);
    }

    /** Merges imported items (e.g. from the browser-only mode) into the user's progress. */
    @Transactional
    public int importItems(Long userId, List<ProgressItem> imported) {
        int count = 0;
        long room = limits.maxProgressItems() - items.countByUserId(userId);
        for (ProgressItem in : imported) {
            if (in.key() == null || in.section() == null) continue;
            if (in.key().length() > MAX_KEY_LENGTH || in.section().length() > MAX_SECTION_LENGTH) continue;
            ItemProgress p = items.findByUserIdAndItemKey(userId, in.key()).orElse(null);
            if (p == null) {
                if (room-- <= 0) throw limitReached();
                p = new ItemProgress(userId, in.key(), in.section());
            }
            p.setDone(p.isDone() || in.done());
            if (in.completedAt() != null && p.isDone()) p.setCompletedAt(in.completedAt());
            p.setRevise(p.isRevise() || in.revise());
            if (in.note() != null && !in.note().isBlank() && in.note().length() <= MAX_NOTE_LENGTH) p.setNote(in.note());
            p.touch();
            items.save(p);
            count++;
        }
        requireNotesWithinLimit(userId);
        return count;
    }

    private ResponseStatusException limitReached() {
        return new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY,
                "This account has reached its limit of " + limits.maxProgressItems() + " tracked items");
    }

    private void requireNotesWithinLimit(Long userId) {
        if (items.totalNoteLength(userId) > limits.maxNoteCharsTotal()) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY,
                    "This account has reached its storage limit for notes. Shorten or delete some notes.");
        }
    }

    @Transactional
    public void reset(Long userId) {
        items.deleteByUserId(userId);
        activity.deleteByUserId(userId);
        quizAttempts.deleteByUserId(userId);
        habitLogs.deleteByUserId(userId);
    }

    @Transactional
    public void recordActivity(Long userId) {
        LocalDate today = LocalDate.now();
        ActivityDay day = activity.findByUserIdAndDay(userId, today).orElseGet(() -> new ActivityDay(userId, today));
        day.increment();
        activity.save(day);
    }
}
