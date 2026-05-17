package dev.juanchi.jvmstartup.orders;

import dev.juanchi.jvmstartup.api.CreateOrderRequest;
import dev.juanchi.jvmstartup.api.OrderResponse;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.NoSuchElementException;

@Service
public class OrderService {

    private final OrderRepository repository;
    private final Clock clock;

    public OrderService(OrderRepository repository, Clock clock) {
        this.repository = repository;
        this.clock = clock;
    }

    public OrderResponse create(CreateOrderRequest request) {
        var entity = new OrderEntity(
                null,
                request.customerCode(),
                request.sku(),
                request.quantity(),
                request.unitPrice(),
                Instant.now(clock)
        );
        return toResponse(repository.save(entity));
    }

    public OrderResponse get(long id) {
        return repository.findById(id)
                .map(OrderService::toResponse)
                .orElseThrow(() -> new NoSuchElementException("Order not found: " + id));
    }

    public long count() {
        return repository.countOrders();
    }

    private static OrderResponse toResponse(OrderEntity entity) {
        return new OrderResponse(
                entity.id(),
                entity.customerCode(),
                entity.sku(),
                entity.quantity(),
                entity.unitPrice(),
                entity.total(),
                entity.createdAt()
        );
    }
}
