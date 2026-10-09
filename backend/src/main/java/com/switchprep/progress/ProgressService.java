package com.switchprep.progress;

import com.switchprep.progress.ProgressDtos.ProgressItem;
import com.switchprep.progress.ProgressDtos.ProgressUpdate;
import com.switchprep.habit.HabitLogRepository;
import com.switchprep.quiz.QuizAttemptRepository;
import java.time.LocalDate;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProgressService {

    private final ItemProgressRepository items;
    private final ActivityDayRepository activity;
    private final QuizAttemptRepository quizAttempts;
    private final HabitLogRepository habitLogs;

    public ProgressService(ItemProgressRepository items, ActivityDayRepository activity,
                           QuizAttemptRepository quizAttempts, HabitLogRepository habitLogs) {
        this.items = items;
        this.activity = activity;
        this.quizAttempts = quizAttempts;
        this.habitLogs = habitLogs;
    }

    @Transactional(readOnly = true)
    public List<ProgressItem> list(Long userId) {
        return items.findByUserId(userId).stream().map(ProgressItem::from).toList();
    }

    @Transactional
    public ProgressItem upsert(Long userId, String key, ProgressUpdate update) {
        ItemProgress p = items.findByUserIdAndItemKey(userId, key)
                .orElseGet(() -> new ItemProgress(userId, key, update.section()));
        boolean wasDone = p.isDone();
        p.setSection(update.section());
        if (update.done() != null) p.setDone(update.done());
        if (update.revise() != null) p.setRevise(update.revise());
        if (update.note() != null) p.setNote(update.note().isBlank() ? null : update.note());
        p.touch();
        ItemProgress saved = items.save(p);
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
        for (ProgressItem in : imported) {
            if (in.key() == null || in.section() == null) continue;
            ItemProgress p = items.findByUserIdAndItemKey(userId, in.key())
                    .orElseGet(() -> new ItemProgress(userId, in.key(), in.section()));
            p.setDone(p.isDone() || in.done());
            if (in.completedAt() != null && p.isDone()) p.setCompletedAt(in.completedAt());
            p.setRevise(p.isRevise() || in.revise());
            if (in.note() != null && !in.note().isBlank()) p.setNote(in.note());
            p.touch();
            items.save(p);
            count++;
        }
        return count;
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
