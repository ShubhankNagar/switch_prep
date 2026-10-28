package com.switchprep.auth;

import com.switchprep.auth.GoogleTokenVerifier.GoogleAccount;
import com.switchprep.config.AppProperties;
import com.switchprep.user.AppUser;
import com.switchprep.user.AppUserRepository;
import com.switchprep.user.UserDto;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.dao.DataIntegrityViolationException;
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
    private final GoogleTokenVerifier google;
    private final AppProperties.Auth auth;

    public AuthController(AppUserRepository users, PasswordEncoder encoder, JwtService jwt,
                          GoogleTokenVerifier google, AppProperties props) {
        this.users = users;
        this.encoder = encoder;
        this.jwt = jwt;
        this.google = google;
        this.auth = props.auth();
    }

    public record RegisterRequest(
            @NotBlank @Size(min = 3, max = 50) @Pattern(regexp = "[a-zA-Z0-9_.-]+") String username,
            @NotBlank @Size(min = 6, max = 100) String password,
            @Size(max = 100) String displayName) {
    }

    public record LoginRequest(@NotBlank String username, @NotBlank String password) {
    }

    /** {@code credential} is the ID token from the Sign in with Google button. */
    public record GoogleLoginRequest(@NotBlank @Size(max = 4096) String credential) {
    }

    public record AuthResponse(String token, UserDto user) {
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public AuthResponse register(@Valid @RequestBody RegisterRequest req) {
        requirePasswordLogin();
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
        requirePasswordLogin();
        AppUser user = users.findByUsername(req.username().toLowerCase())
                .filter(u -> u.getPasswordHash() != null && encoder.matches(req.password(), u.getPasswordHash()))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid username or password"));
        return new AuthResponse(jwt.issue(user.getId(), user.getUsername()), UserDto.from(user));
    }

    /** Signs in with Google, creating the account on first use. The account is tied to Google's stable user id. */
    @PostMapping("/google")
    public AuthResponse google(@Valid @RequestBody GoogleLoginRequest req) {
        if (!auth.googleEnabled()) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Google sign-in is not set up on this server");
        }
        GoogleAccount account = google.verify(req.credential())
                .filter(a -> a.subject() != null && AppUser.googleUsername(a.subject()).length() <= 50)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Google sign-in failed. Please try again."));
        AppUser user = users.findByGoogleSub(account.subject())
                .map(existing -> refreshEmail(existing, account))
                .orElseGet(() -> createGoogleUser(account));
        return new AuthResponse(jwt.issue(user.getId(), user.getUsername()), UserDto.from(user));
    }

    private AppUser refreshEmail(AppUser user, GoogleAccount account) {
        if (account.email().equals(user.getEmail())) return user;
        user.setEmail(account.email());
        return users.save(user);
    }

    private AppUser createGoogleUser(GoogleAccount account) {
        String name = account.name() == null || account.name().isBlank()
                ? account.email().substring(0, account.email().indexOf('@'))
                : account.name();
        try {
            return users.save(AppUser.fromGoogle(account.subject(), account.email(),
                    name.length() > 100 ? name.substring(0, 100) : name));
        } catch (DataIntegrityViolationException e) {
            // two first sign-ins raced; the other request created the account
            return users.findByGoogleSub(account.subject()).orElseThrow(() -> e);
        }
    }

    private void requirePasswordLogin() {
        if (!auth.passwordLogin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Password sign-in is switched off. Sign in with Google.");
        }
    }
}
