package dev.juanchi.jvmstartup.work;

import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.zip.CRC32;

@Service
public class WorkService {

    private static final int MAX_ITERATIONS = 5_000;

    public WorkResponse execute(String input, int iterations, long orderCount) {
        int boundedIterations = Math.max(1, Math.min(iterations, MAX_ITERATIONS));
        long start = System.nanoTime();
        long score = calculateScore(input, boundedIterations);
        long elapsedMicros = (System.nanoTime() - start) / 1_000;
        return new WorkResponse(input, boundedIterations, score, orderCount, elapsedMicros);
    }

    public long calculateScore(String input, int iterations) {
        byte[] seed = input.getBytes(StandardCharsets.UTF_8);
        long score = 17;
        for (int i = 0; i < iterations; i++) {
            CRC32 crc = new CRC32();
            crc.update(seed);
            crc.update(longToBytes(score + i));
            score = Long.rotateLeft(score ^ crc.getValue(), 7) + 0x9E3779B97F4A7C15L;
        }
        return score & Long.MAX_VALUE;
    }

    private static byte[] longToBytes(long value) {
        return new byte[]{
                (byte) (value >>> 56),
                (byte) (value >>> 48),
                (byte) (value >>> 40),
                (byte) (value >>> 32),
                (byte) (value >>> 24),
                (byte) (value >>> 16),
                (byte) (value >>> 8),
                (byte) value
        };
    }
}
