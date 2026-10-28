package com.switchprep.auth;

import com.switchprep.config.AppProperties;
import java.util.Optional;
import java.util.Set;
import java.util.function.Predicate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2TokenValidatorResult;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtException;
import org.springframework.security.oauth2.jwt.JwtTimestampValidator;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.stereotype.Component;

/**
 * Verifies Google ID tokens locally: signature against Google's published keys (fetched on first use and cached),
 * expiry, issuer, that the token was issued for our client ID, and that Google has verified the email address.
 */
@Component
public class NimbusGoogleTokenVerifier implements GoogleTokenVerifier {

    private static final String GOOGLE_KEYS_URI = "https://www.googleapis.com/oauth2/v3/certs";
    private static final Set<String> GOOGLE_ISSUERS = Set.of("https://accounts.google.com", "accounts.google.com");

    private final boolean enabled;
    private final NimbusJwtDecoder decoder;

    @Autowired
    public NimbusGoogleTokenVerifier(AppProperties props) {
        this(props.auth().googleClientId(), GOOGLE_KEYS_URI);
    }

    /** For tests, which serve their own signing keys. */
    NimbusGoogleTokenVerifier(String clientId, String keysUri) {
        this.enabled = clientId != null && !clientId.isBlank();
        this.decoder = NimbusJwtDecoder.withJwkSetUri(keysUri).build();
        this.decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
                new JwtTimestampValidator(),
                require("issuer is not Google", jwt -> GOOGLE_ISSUERS.contains(jwt.getClaimAsString("iss"))),
                require("token was issued for another app",
                        jwt -> jwt.getAudience() != null && jwt.getAudience().contains(clientId)),
                require("email is not verified", jwt -> Boolean.TRUE.equals(jwt.getClaimAsBoolean("email_verified"))
                        && jwt.getClaimAsString("email") != null)));
    }

    @Override
    public Optional<GoogleAccount> verify(String idToken) {
        if (!enabled) return Optional.empty();
        try {
            Jwt jwt = decoder.decode(idToken);
            return Optional.of(new GoogleAccount(jwt.getSubject(), jwt.getClaimAsString("email"),
                    jwt.getClaimAsString("name")));
        } catch (JwtException e) {
            return Optional.empty();
        }
    }

    private static OAuth2TokenValidator<Jwt> require(String failure, Predicate<Jwt> check) {
        return jwt -> check.test(jwt)
                ? OAuth2TokenValidatorResult.success()
                : OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_token", failure, null));
    }
}
