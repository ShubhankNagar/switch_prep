package com.switchprep.auth;

import com.switchprep.user.AppUser;
import com.switchprep.user.AppUserRepository;
import com.switchprep.user.UserDto;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AppUserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;

    public AuthController(AppUserRepository users, PasswordEncoder encoder, JwtService jwt) {
        this.users = users;
        this.encoder = encoder;
        this.jwt = jwt;
    }

    public record RegisterRequest(
            @NotBlank @Size(min = 3, max = 50) @Pattern(regexp = "[a-zA-Z0-9_.-]+") String username,
            @NotBlank @Size(min = 6, max = 100) String password,
            @Size(max = 100) String displayName) {
    }

    public record LoginRequest(@NotBlank String username, @NotBlank String password) {
    }

    public record AuthResponse(String token, UserDto user) {
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public AuthResponse register(@Valid @RequestBody RegisterRequest req) {
        String username = req.username().toLowerCase();
        if (users.existsByUsername(username)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Username already taken");
        }
        String name = req.displayName() == null || req.displayName().isBlank() ? req.username() : req.displayName();
        AppUser user = users.save(new AppUser(username, encoder.encode(req.password()), name));
        return new AuthResponse(jwt.issue(user.getId(), user.getUsername()), UserDto.from(user));
    }

    @PostMapping("/login")
    public AuthResponse login(@Valid @RequestBody LoginRequest req) {
        AppUser user = users.findByUsername(req.username().toLowerCase())
                .filter(u -> encoder.matches(req.password(), u.getPasswordHash()))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid username or password"));
        return new AuthResponse(jwt.issue(user.getId(), user.getUsername()), UserDto.from(user));
    }
}
