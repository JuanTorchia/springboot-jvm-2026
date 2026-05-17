package dev.juanchi.jvmstartup.work;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WorkServiceTest {

    @Test
    void calculatesStableScoreForSameInputAndIterations() {
        var service = new WorkService();

        var first = service.calculateScore("spring-aot", 300);
        var second = service.calculateScore("spring-aot", 300);

        assertThat(first).isEqualTo(second);
        assertThat(first).isGreaterThan(0);
    }

    @Test
    void capsIterationsToKeepBenchmarkControlled() {
        var service = new WorkService();

        var response = service.execute("payload", 99_999, 7);

        assertThat(response.iterations()).isEqualTo(5_000);
        assertThat(response.orderCount()).isEqualTo(7);
    }
}
