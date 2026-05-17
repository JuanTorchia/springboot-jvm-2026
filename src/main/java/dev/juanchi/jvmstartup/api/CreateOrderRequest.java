package dev.juanchi.jvmstartup.api;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record CreateOrderRequest(
        @NotBlank @Size(max = 32) String customerCode,
        @NotBlank @Size(max = 64) String sku,
        @Min(1) @Max(100) int quantity,
        @DecimalMin("0.01") BigDecimal unitPrice
) {
}
