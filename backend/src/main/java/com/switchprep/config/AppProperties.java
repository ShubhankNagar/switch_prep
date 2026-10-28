package com.switchprep.config;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app")
public record AppProperties(boolean production, Jwt jwt, Cors cors, Auth auth, Limits limits) {

    /**
     * With {@code app.production} on (the prod profile), refuses to start with missing or development settings.
     * Needed because Spring leaves an unset {@code ${VARIABLE}} in a bound property as literal text instead of failing.
     */
    public AppProperties {
        if (production) {
            List<String> problems = new ArrayList<>();
            if (unset(jwt.secret()) || jwt.secret().length() < 32 || jwt.secret().startsWith("change-me")) {
                problems.add("APP_JWT_SECRET must be a random value of at least 32 characters");
            }
            if (unset(auth.googleClientId())) {
                problems.add("APP_GOOGLE_CLIENT_ID must be the OAuth client ID from Google Cloud console");
            }
            List<String> origins = cors.allowedOrigins();
            if (origins == null || origins.isEmpty() || origins.stream().anyMatch(o -> unset(o) || o.contains("*"))) {
                problems.add("APP_CORS_ORIGINS must list the exact site origin(s), for example https://name.github.io");
            }
            if (!problems.isEmpty()) {
                throw new IllegalStateException("Production settings are incomplete: " + String.join("; ", problems));
            }
        }
    }

    private static boolean unset(String value) {
        return value == null || value.isBlank() || value.contains("${");
    }

    public record Jwt(String secret, int expirationDays) {
    }

    public record Cors(List<String> allowedOrigins) {
    }

    public record Auth(boolean passwordLogin, String googleClientId) {

        public boolean googleEnabled() {
            return googleClientId != null && !googleClientId.isBlank();
        }
    }

    /** Per-user caps that keep one account from filling a small shared database. */
    public record Limits(int maxProgressItems, long maxNoteCharsTotal, int maxQuizAttempts, long maxRequestBytes) {
    }
}
