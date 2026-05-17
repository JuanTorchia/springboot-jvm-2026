package dev.juanchi.jvmstartup.work;

public record WorkResponse(
        String input,
        int iterations,
        long score,
        long orderCount,
        long elapsedMicros
) {
}
