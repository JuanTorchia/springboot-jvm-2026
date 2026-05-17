package dev.juanchi.jvmstartup.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

@Configuration
class RuntimeConfig {

    @Bean
    Clock clock() {
        return Clock.systemUTC();
    }
}
