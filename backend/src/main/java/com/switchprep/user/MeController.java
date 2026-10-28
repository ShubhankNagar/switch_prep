package com.switchprep.user;

import com.switchprep.auth.CurrentUser;
import com.switchprep.habit.HabitSettingsRepository;
import com.switchprep.progress.ProgressService;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/me")
public class MeController {

    private final CurrentUser currentUser;
    private final AppUserRepository userRepository;
    private final ProgressService progressService;
    private final HabitSettingsRepository habitSettings;

    public MeController(CurrentUser currentUser, AppUserRepository userRepository, ProgressService progressService,
                        HabitSettingsRepository habitSettings) {
        this.currentUser = currentUser;
        this.userRepository = userRepository;
        this.progressService = progressService;
        this.habitSettings = habitSettings;
    }

    public record UpdateMeRequest(@Size(max = 100) String displayName, LocalDate startDate) {
    }

    @GetMapping
    public UserDto me() {
        return UserDto.from(currentUser.get());
    }

    @PutMapping
    public UserDto update(@RequestBody UpdateMeRequest req) {
        AppUser user = currentUser.get();
        if (req.displayName() != null) user.setDisplayName(req.displayName());
        if (req.startDate() != null) user.setStartDate(req.startDate());
        return UserDto.from(userRepository.save(user));
    }

    /** Deletes the account and everything stored for it. */
    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Transactional
    public void delete() {
        AppUser user = currentUser.get();
        progressService.reset(user.getId());
        habitSettings.deleteById(user.getId());
        userRepository.delete(user);
    }
}
