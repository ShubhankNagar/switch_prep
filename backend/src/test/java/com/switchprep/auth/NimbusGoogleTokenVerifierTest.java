package com.switchprep.auth;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.gen.RSAKeyGenerator;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import com.sun.net.httpserver.HttpServer;
import com.switchprep.auth.GoogleTokenVerifier.GoogleAccount;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;
import java.util.function.Consumer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/** Runs the real verifier against tokens signed here, with the signing key served the way Google serves its keys. */
class NimbusGoogleTokenVerifierTest {

    private static final String CLIENT_ID = "our-app.apps.googleusercontent.com";

    private static HttpServer keyServer;
    private static RSAKey trustedKey;
    private static RSAKey strangerKey;
    private static NimbusGoogleTokenVerifier verifier;

    @BeforeAll
    static void startKeyServer() throws Exception {
        trustedKey = new RSAKeyGenerator(2048).keyID("trusted").generate();
        strangerKey = new RSAKeyGenerator(2048).keyID("trusted").generate();
        byte[] jwks = new JWKSet(trustedKey.toPublicJWK()).toString().getBytes(StandardCharsets.UTF_8);
        keyServer = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        keyServer.createContext("/certs", exchange -> {
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, jwks.length);
            exchange.getResponseBody().write(jwks);
            exchange.close();
        });
        keyServer.start();
        verifier = new NimbusGoogleTokenVerifier(CLIENT_ID,
                "http://127.0.0.1:" + keyServer.getAddress().getPort() + "/certs");
    }

    @AfterAll
    static void stopKeyServer() {
        keyServer.stop(0);
    }

    /** A token exactly as Google issues it, changed by {@code tweak}, signed with {@code key}. */
    private static String token(RSAKey key, Consumer<JWTClaimsSet.Builder> tweak) throws Exception {
        JWTClaimsSet.Builder claims = new JWTClaimsSet.Builder()
                .issuer("https://accounts.google.com")
                .audience(CLIENT_ID)
                .subject("109876543210987654321")
                .claim("email", "asha@example.com")
                .claim("email_verified", true)
                .claim("name", "Asha Rao")
                .issueTime(Date.from(Instant.now()))
                .expirationTime(Date.from(Instant.now().plusSeconds(3600)));
        tweak.accept(claims);
        SignedJWT jwt = new SignedJWT(new JWSHeader.Builder(JWSAlgorithm.RS256).keyID(key.getKeyID()).build(), claims.build());
        jwt.sign(new RSASSASigner(key));
        return jwt.serialize();
    }

    @Test
    void acceptsAGenuineToken() throws Exception {
        Optional<GoogleAccount> account = verifier.verify(token(trustedKey, c -> { }));
        assertTrue(account.isPresent());
        assertEquals("109876543210987654321", account.get().subject());
        assertEquals("asha@example.com", account.get().email());
        assertEquals("Asha Rao", account.get().name());
    }

    @Test
    void acceptsGooglesShortIssuerForm() throws Exception {
        assertTrue(verifier.verify(token(trustedKey, c -> c.issuer("accounts.google.com"))).isPresent());
    }

    @Test
    void rejectsATokenSignedBySomeoneElse() throws Exception {
        assertTrue(verifier.verify(token(strangerKey, c -> { })).isEmpty());
    }

    @Test
    void rejectsATokenIssuedForAnotherApp() throws Exception {
        assertTrue(verifier.verify(token(trustedKey, c -> c.audience("another-app.apps.googleusercontent.com"))).isEmpty());
    }

    @Test
    void rejectsAnotherIssuer() throws Exception {
        assertTrue(verifier.verify(token(trustedKey, c -> c.issuer("https://evil.example.com"))).isEmpty());
    }

    @Test
    void rejectsAnExpiredToken() throws Exception {
        assertTrue(verifier.verify(token(trustedKey,
                c -> c.expirationTime(Date.from(Instant.now().minusSeconds(600))))).isEmpty());
    }

    @Test
    void rejectsAnUnverifiedEmail() throws Exception {
        assertTrue(verifier.verify(token(trustedKey, c -> c.claim("email_verified", false))).isEmpty());
    }

    @Test
    void rejectsGarbage() {
        assertTrue(verifier.verify("not-a-token").isEmpty());
    }

    @Test
    void rejectsEverythingWhenNoClientIdIsConfigured() throws Exception {
        NimbusGoogleTokenVerifier unconfigured = new NimbusGoogleTokenVerifier("",
                "http://127.0.0.1:" + keyServer.getAddress().getPort() + "/certs");
        assertTrue(unconfigured.verify(token(trustedKey, c -> c.audience(""))).isEmpty());
    }
}
