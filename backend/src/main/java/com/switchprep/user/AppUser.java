package com.switchprep.user;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "app_user")
public class AppUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 50)
    private String username;

    /** Null for accounts that sign in with Google. */
    private String passwordHash;

    /** Google's stable id for the account ("sub" claim); null for password accounts. */
    @Column(unique = true)
    private String googleSub;

    /** Email from Google, shown in the UI. Not an identifier: it can change, googleSub cannot. */
    @Column(length = 254)
    private String email;

    @Column(length = 100)
    private String displayName;

    /** Day 1 of the 60-day plan. */
    private LocalDate startDate;

    @Column(nullable = false)
    private Instant createdAt = Instant.now();

    protected AppUser() {
    }

    public AppUser(String username, String passwordHash, String displayName) {
        this.username = username;
        this.passwordHash = passwordHash;
        this.displayName = displayName;
        this.startDate = LocalDate.now();
    }

    public static AppUser fromGoogle(String googleSub, String email, String displayName) {
        AppUser user = new AppUser(googleUsername(googleSub), null, displayName);
        user.googleSub = googleSub;
        user.email = email;
        return user;
    }

    /** Password usernames cannot contain ':', so these never clash with them. */
    public static String googleUsername(String googleSub) {
        return "g:" + googleSub;
    }

    public Long getId() { return id; }
    public String getUsername() { return username; }
    public String getPasswordHash() { return passwordHash; }
    public String getGoogleSub() { return googleSub; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getDisplayName() { return displayName; }
    public void setDisplayName(String displayName) { this.displayName = displayName; }
    public LocalDate getStartDate() { return startDate; }
    public void setStartDate(LocalDate startDate) { this.startDate = startDate; }
    public Instant getCreatedAt() { return createdAt; }
}
