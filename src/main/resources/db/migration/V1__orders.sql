create table orders (
    id bigserial primary key,
    customer_code varchar(32) not null,
    sku varchar(64) not null,
    quantity integer not null,
    unit_price numeric(12, 2) not null,
    created_at timestamp with time zone not null
);

create index idx_orders_customer_code on orders(customer_code);
