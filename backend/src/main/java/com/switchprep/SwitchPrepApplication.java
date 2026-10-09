package com.switchprep;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SwitchPrepApplication {

    public static void main(String[] args) {
        SpringApplication.run(SwitchPrepApplication.class, args);
    }
}
