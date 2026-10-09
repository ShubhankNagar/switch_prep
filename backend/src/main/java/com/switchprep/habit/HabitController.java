package com.switchprep.habit;

import com.switchprep.auth.CurrentUser;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import jakarta.validation.Valid;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Daily routine: habit definitions plus one log row per day. */
@RestController
@RequestMapping("/api")
public class HabitController {

    private final HabitSettingsRepository settings;
    private final HabitLogRepository logs;
    private final CurrentUser currentUser;

    public HabitController(HabitSettingsRepository settings, HabitLogRepository logs, CurrentUser currentUser) {
        this.settings = settings;
        this.logs = logs;
        this.currentUser = currentUser;
    }

    public record HabitsDto(String habitsJson, Instant updatedAt) {
    }

    public record HabitsRequest(@NotNull @Size(max = 50000) String habitsJson) {
    }

    public record LogDto(LocalDate date, String valuesJson, int minutes, String journal, Instant updatedAt) {
        static LogDto from(HabitLog l) {
            return new LogDto(l.getLogDate(), l.getValuesJson(), l.getMinutes(), l.getJournal(), l.getUpdatedAt());
        }
    }

    public record LogRequest(@Size(max = 10000) String valuesJson, @Min(0) @Max(1440) Integer minutes,
                             @Size(max = 1000) String journal) {
    }

    /** Returns 204 when the user has never saved habits, so the client falls back to its defaults. */
    @GetMapping("/habits")
    public ResponseEntity<HabitsDto> getHabits() {
        return settings.findById(currentUser.id())
                .map(s -> ResponseEntity.ok(new HabitsDto(s.getHabitsJson(), s.getUpdatedAt())))
                .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @PutMapping("/habits")
    @Transactional
    public HabitsDto saveHabits(@Valid @RequestBody HabitsRequest req) {
        Long userId = currentUser.id();
        HabitSettings s = settings.findById(userId).orElseGet(() -> new HabitSettings(userId, req.habitsJson()));
        s.setHabitsJson(req.habitsJson());
        HabitSettings saved = settings.save(s);
        return new HabitsDto(saved.getHabitsJson(), saved.getUpdatedAt());
    }

    @GetMapping("/habit-logs")
    public List<LogDto> getLogs(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        Long userId = currentUser.id();
        List<HabitLog> rows = from != null && to != null
                ? logs.findByUserIdAndLogDateBetweenOrderByLogDateAsc(userId, from, to)
                : logs.findByUserIdOrderByLogDateAsc(userId);
        return rows.stream().map(LogDto::from).toList();
    }

    /** Partial update of one day's log: null fields are left unchanged. */
    @PutMapping("/habit-logs/{date}")
    @Transactional
    public LogDto saveLog(@PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date,
                          @Valid @RequestBody LogRequest req) {
        Long userId = currentUser.id();
        HabitLog log = logs.findByUserIdAndLogDate(userId, date).orElseGet(() -> new HabitLog(userId, date));
        if (req.valuesJson() != null) log.setValuesJson(req.valuesJson());
        if (req.minutes() != null) log.setMinutes(req.minutes());
        if (req.journal() != null) log.setJournal(req.journal().isBlank() ? null : req.journal());
        log.touch();
        return LogDto.from(logs.save(log));
    }
}
