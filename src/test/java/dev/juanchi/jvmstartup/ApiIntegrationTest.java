package dev.juanchi.jvmstartup;

import dev.juanchi.jvmstartup.api.CreateOrderRequest;
import dev.juanchi.jvmstartup.api.WorkRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.math.BigDecimal;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ApiIntegrationTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17-alpine");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    TestRestTemplate rest;

    @Test
    void pingReturnsStableHealthShape() {
        var response = rest.getForEntity("/api/ping", Map.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsEntry("status", "ok");
        assertThat(response.getBody()).containsKey("timestamp");
    }

    @Test
    void createAndFetchOrderRoundTripUsesPostgres() {
        var request = new CreateOrderRequest("ACME-42", "book-stand", 3, new BigDecimal("19.95"));

        var created = rest.postForEntity("/api/orders", request, Map.class);
        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(created.getBody()).containsEntry("customerCode", "ACME-42");

        var id = created.getBody().get("id");
        var fetched = rest.getForEntity("/api/orders/" + id, Map.class);

        assertThat(fetched.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(fetched.getBody()).containsEntry("sku", "book-stand");
        assertThat(fetched.getBody()).containsEntry("quantity", 3);
    }

    @Test
    void validationRejectsInvalidJsonPayload() {
        var request = new CreateOrderRequest("", "x", 0, new BigDecimal("-1.00"));

        var response = rest.postForEntity("/api/orders", request, Map.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).containsKey("errors");
    }

    @Test
    void workEndpointReturnsDeterministicResultShape() {
        var response = rest.postForEntity("/api/work", new WorkRequest("senior-java", 250), Map.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsKeys("input", "iterations", "score", "orderCount", "elapsedMicros");
        assertThat(response.getBody()).containsEntry("input", "senior-java");
        assertThat(response.getBody()).containsEntry("iterations", 250);
    }
}
