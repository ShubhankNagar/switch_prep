package com.switchprep.quiz;

import com.switchprep.auth.CurrentUser;
import com.switchprep.config.AppProperties;
import com.switchprep.progress.ProgressService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/quiz-attempts")
public class QuizController {

    private final QuizAttemptRepository attempts;
    private final ProgressService progressService;
    private final CurrentUser currentUser;
    private final int maxAttempts;

    public QuizController(QuizAttemptRepository attempts, ProgressService progressService, CurrentUser currentUser,
                          AppProperties props) {
        this.attempts = attempts;
        this.progressService = progressService;
        this.currentUser = currentUser;
        this.maxAttempts = props.limits().maxQuizAttempts();
    }

    public record AttemptRequest(@NotBlank @Size(max = 150) String quizKey, @Min(0) int score, @Min(1) int total,
                                 @Size(max = 20000) String answersJson, int durationSeconds, Instant takenAt) {
    }

    public record AttemptDto(Long id, String quizKey, int score, int total, String answersJson,
                             int durationSeconds, Instant takenAt) {
        static AttemptDto from(QuizAttempt a) {
            return new AttemptDto(a.getId(), a.getQuizKey(), a.getScore(), a.getTotal(), a.getAnswersJson(),
                    a.getDurationSeconds(), a.getTakenAt());
        }
    }

    @GetMapping
    public List<AttemptDto> list() {
        return attempts.findByUserIdOrderByTakenAtDesc(currentUser.id()).stream().map(AttemptDto::from).toList();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public AttemptDto create(@Valid @RequestBody AttemptRequest req) {
        Long userId = currentUser.id();
        if (attempts.countByUserId(userId) >= maxAttempts) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY,
                    "This account has reached its limit of " + maxAttempts + " saved quiz attempts");
        }
        QuizAttempt a = new QuizAttempt(userId, req.quizKey(), Math.min(req.score(), req.total()), req.total(),
                req.answersJson(), Math.max(0, req.durationSeconds()));
        if (req.takenAt() != null) {
            a.setTakenAt(req.takenAt()); // imported attempt from browser-only mode
        } else {
            progressService.recordActivity(userId);
        }
        return AttemptDto.from(attempts.save(a));
    }
}
