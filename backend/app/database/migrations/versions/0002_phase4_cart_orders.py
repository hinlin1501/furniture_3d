"""phase 4: cart, payments, orders

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-08 16:40:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('carts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_carts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_carts')),
    sa.UniqueConstraint('user_id', name=op.f('uq_carts_user_id'))
    )
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('method', sa.String(length=30), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'EXPIRED', 'REFUNDED', name='payment_status', native_enum=False, create_constraint=True, length=20), server_default='PENDING', nullable=False),
    sa.Column('snapshot', sa.JSON(), nullable=False),
    sa.Column('gateway_ref', sa.String(length=64), nullable=False),
    sa.Column('failure_reason', sa.String(length=255), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_payments_amount_positive')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_payments_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payments')),
    sa.UniqueConstraint('gateway_ref', name=op.f('uq_payments_gateway_ref'))
    )
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_table('cart_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cart_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_cart_items_quantity_positive')),
    sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], name=op.f('fk_cart_items_cart_id_carts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_cart_items_product_id_products'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cart_items')),
    sa.UniqueConstraint('cart_id', 'product_id', name='uq_cart_items_cart_product')
    )
    op.create_index(op.f('ix_cart_items_cart_id'), 'cart_items', ['cart_id'], unique=False)
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('payment_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('CONFIRMED', 'PREPARING', 'SHIPPING', 'COMPLETED', name='order_status', native_enum=False, create_constraint=True, length=20), server_default='CONFIRMED', nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('recipient_name', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('shipping_address', sa.Text(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('total_amount > 0', name=op.f('ck_orders_total_positive')),
    sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], name=op.f('fk_orders_payment_id_payments'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_orders_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_orders')),
    sa.UniqueConstraint('code', name=op.f('uq_orders_code')),
    sa.UniqueConstraint('payment_id', name=op.f('uq_orders_payment_id'))
    )
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_table('order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('product_name', sa.String(length=255), nullable=False),
    sa.Column('image_url', sa.String(length=1024), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_order_items_quantity_positive')),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_items_order_id_orders'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_order_items_product_id_products'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_order_items'))
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_table('order_status_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('CONFIRMED', 'PREPARING', 'SHIPPING', 'COMPLETED', name='order_history_status', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_status_history_order_id_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_order_status_history'))
    )
    op.create_index(op.f('ix_order_status_history_order_id'), 'order_status_history', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_status_history_order_id'), table_name='order_status_history')
    op.drop_table('order_status_history')
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_cart_items_cart_id'), table_name='cart_items')
    op.drop_table('cart_items')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_table('payments')
    op.drop_table('carts')