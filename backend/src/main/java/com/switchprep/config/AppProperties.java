package com.switchprep.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app")
public record AppProperties(Jwt jwt, Cors cors) {

    public record Jwt(String secret, int expirationDays) {
    }

    public record Cors(List<String> allowedOrigins) {
    }
}
