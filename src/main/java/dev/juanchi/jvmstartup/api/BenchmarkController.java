package dev.juanchi.jvmstartup.api;

import dev.juanchi.jvmstartup.orders.OrderService;
import dev.juanchi.jvmstartup.work.WorkResponse;
import dev.juanchi.jvmstartup.work.WorkService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
public class BenchmarkController {

    private final OrderService orders;
    private final WorkService work;

    public BenchmarkController(OrderService orders, WorkService work) {
        this.orders = orders;
        this.work = work;
    }

    @GetMapping("/api/ping")
    Map<String, Object> ping() {
        return Map.of(
                "status", "ok",
                "timestamp", Instant.now().toString()
        );
    }

    @PostMapping("/api/orders")
    @ResponseStatus(HttpStatus.CREATED)
    OrderResponse createOrder(@Valid @RequestBody CreateOrderRequest request) {
        return orders.create(request);
    }

    @GetMapping("/api/orders/{id}")
    OrderResponse getOrder(@PathVariable long id) {
        return orders.get(id);
    }

    @PostMapping("/api/work")
    WorkResponse doWork(@Valid @RequestBody WorkRequest request) {
        return work.execute(request.input(), request.iterations(), orders.count());
    }
}
