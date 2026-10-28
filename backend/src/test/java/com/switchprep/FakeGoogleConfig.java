package com.switchprep;

import com.switchprep.auth.GoogleTokenVerifier;
import java.util.Optional;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

/** Replaces the real Google check in tests: "google:{sub}:{email}:{name}" is a valid token, anything else is not. */
@TestConfiguration
public class FakeGoogleConfig {

    @Bean
    @Primary
    GoogleTokenVerifier fakeGoogleTokenVerifier() {
        return idToken -> {
            String[] parts = idToken.split(":");
            if (parts.length != 4 || !parts[0].equals("google")) return Optional.empty();
            return Optional.of(new GoogleTokenVerifier.GoogleAccount(parts[1], parts[2], parts[3]));
        };
    }
}
