package dev.juanchi.jvmstartup.api;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record WorkRequest(
        @NotBlank @Size(max = 128) String input,
        @Min(1) @Max(5_000) int iterations
) {
}
