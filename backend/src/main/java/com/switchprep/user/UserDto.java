package com.switchprep.user;

import java.time.LocalDate;

public record UserDto(Long id, String username, String displayName, LocalDate startDate) {

    public static UserDto from(AppUser u) {
        return new UserDto(u.getId(), u.getUsername(), u.getDisplayName(), u.getStartDate());
    }
}
