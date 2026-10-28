package com.switchprep.auth;

import java.util.Optional;

/** Checks the ID token ("credential") that the Sign in with Google button hands to the browser. */
public interface GoogleTokenVerifier {

    record GoogleAccount(String subject, String email, String name) {
    }

    /** Returns the Google account the token was issued for, or empty if the token is not valid for this app. */
    Optional<GoogleAccount> verify(String idToken);
}
