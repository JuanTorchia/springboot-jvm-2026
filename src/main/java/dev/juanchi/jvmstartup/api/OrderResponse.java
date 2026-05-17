package dev.juanchi.jvmstartup.api;

import java.math.BigDecimal;
import java.time.Instant;

public record OrderResponse(
        Long id,
        String customerCode,
        String sku,
        int quantity,
        BigDecimal unitPrice,
        BigDecimal total,
        Instant createdAt
) {
}
