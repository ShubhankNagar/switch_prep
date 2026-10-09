package com.switchprep.stats;

import com.switchprep.auth.CurrentUser;
import com.switchprep.progress.ActivityDay;
import com.switchprep.progress.ActivityDayRepository;
import com.switchprep.progress.ItemProgressRepository;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/stats")
public class StatsController {

    private final ItemProgressRepository items;
    private final ActivityDayRepository activity;
    private final CurrentUser currentUser;

    public StatsController(ItemProgressRepository items, ActivityDayRepository activity, CurrentUser currentUser) {
        this.items = items;
        this.activity = activity;
        this.currentUser = currentUser;
    }

    public record DayCount(LocalDate date, int count) {
    }

    public record Stats(Map<String, Long> doneBySection, long totalDone, int currentStreak, int longestStreak,
                        List<DayCount> activity) {
    }

    @GetMapping
    public Stats stats() {
        Long userId = currentUser.id();
        Map<String, Long> bySection = new LinkedHashMap<>();
        for (Object[] row : items.countDoneBySection(userId)) {
            bySection.put((String) row[0], (Long) row[1]);
        }
        long total = bySection.values().stream().mapToLong(Long::longValue).sum();
        List<ActivityDay> days = activity.findByUserIdOrderByDayAsc(userId);
        List<DayCount> counts = days.stream().map(d -> new DayCount(d.getDay(), d.getActions())).toList();
        Set<LocalDate> active = days.stream().map(ActivityDay::getDay).collect(Collectors.toSet());
        return new Stats(bySection, total, currentStreak(active, LocalDate.now()), longestStreak(days), counts);
    }

    /** Consecutive active days ending today (or yesterday, so the streak survives until today's work is done). */
    static int currentStreak(Set<LocalDate> active, LocalDate today) {
        LocalDate d = active.contains(today) ? today : today.minusDays(1);
        int streak = 0;
        while (active.contains(d)) {
            streak++;
            d = d.minusDays(1);
        }
        return streak;
    }

    static int longestStreak(List<ActivityDay> sortedDays) {
        int best = 0;
        int run = 0;
        LocalDate prev = null;
        for (ActivityDay day : sortedDays) {
            run = prev != null && prev.plusDays(1).equals(day.getDay()) ? run + 1 : 1;
            best = Math.max(best, run);
            prev = day.getDay();
        }
        return best;
    }
}
