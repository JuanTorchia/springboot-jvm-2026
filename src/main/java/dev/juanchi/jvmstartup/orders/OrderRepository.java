package dev.juanchi.jvmstartup.orders;

import org.springframework.data.jdbc.repository.query.Query;
import org.springframework.data.repository.CrudRepository;

public interface OrderRepository extends CrudRepository<OrderEntity, Long> {

    @Query("select count(*) from orders")
    long countOrders();
}
