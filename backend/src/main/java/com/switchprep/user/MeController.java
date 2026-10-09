package com.switchprep.user;

import com.switchprep.auth.CurrentUser;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/me")
public class MeController {

    private final CurrentUser currentUser;
    private final AppUserRepository userRepository;

    public MeController(CurrentUser currentUser, AppUserRepository userRepository) {
        this.currentUser = currentUser;
        this.userRepository = userRepository;
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
}
