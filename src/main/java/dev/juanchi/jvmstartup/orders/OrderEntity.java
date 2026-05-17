package dev.juanchi.jvmstartup.orders;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;

@Table("orders")
public record OrderEntity(
        @Id Long id,
        String customerCode,
        String sku,
        int quantity,
        BigDecimal unitPrice,
        Instant createdAt
) {
    public BigDecimal total() {
        return unitPrice.multiply(BigDecimal.valueOf(quantity));
    }
}
