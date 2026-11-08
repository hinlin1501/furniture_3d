# Schema report

## Enum types


## Row counts

- ai.interactions: 0
- ai.product_embeddings: 0
- ai.recommendations: 0
- ai.space_embeddings: 0
- ai.user_preferences: 0
- analytics.sales_kpi_summaries: 0
- ecommerce.cart_items: 0
- ecommerce.carts: 0
- ecommerce.categories: 39
- ecommerce.materials: 11
- ecommerce.order_items: 0
- ecommerce.orders: 0
- ecommerce.product_categories: 235
- ecommerce.product_dimensions: 235
- ecommerce.product_images: 235
- ecommerce.product_materials: 257
- ecommerce.product_models: 0
- ecommerce.product_space_types: 235
- ecommerce.product_styles: 0
- ecommerce.products: 235
- ecommerce.reviews: 0
- ecommerce.space_types: 6
- ecommerce.styles: 0
- ecommerce.users: 13
- public.alembic_version: 1
- public.categories: 0
- public.product_attributes: 0
- public.product_dimensions: 0
- public.product_images: 0
- public.product_models: 0
- public.products: 0
- public.users: 0
- spatial.space_images: 0
- spatial.space_objects: 0
- spatial.spaces: 0
- spatial.spatial_validations: 0

## Columns


### ai.interactions

| column | type | null | default |
|---|---|---|---|
| interaction_id | bigint | NO |  |
| user_id | bigint | NO |  |
| product_id | bigint | NO |  |
| interaction_type | character varying(50) | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ai.product_embeddings

| column | type | null | default |
|---|---|---|---|
| embedding_id | bigint | NO |  |
| product_id | bigint | NO |  |
| embedding_type | character varying(50) | NO |  |
| model_name | character varying(100) | NO |  |
| embedding | vector | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ai.recommendations

| column | type | null | default |
|---|---|---|---|
| recommendation_id | bigint | NO |  |
| user_id | bigint | NO |  |
| space_id | bigint | YES |  |
| product_id | bigint | NO |  |
| score | numeric | YES |  |
| reason | text | YES |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ai.space_embeddings

| column | type | null | default |
|---|---|---|---|
| embedding_id | bigint | NO |  |
| image_id | bigint | NO |  |
| embedding_type | character varying(50) | NO |  |
| model_name | character varying(100) | NO |  |
| embedding_version | character varying(50) | YES |  |
| embedding | vector | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ai.user_preferences

| column | type | null | default |
|---|---|---|---|
| preference_id | bigint | NO |  |
| user_id | bigint | NO |  |
| category_id | bigint | YES |  |
| style_id | bigint | YES |  |
| material_id | bigint | YES |  |

### analytics.sales_kpi_summaries

| column | type | null | default |
|---|---|---|---|
| kpi_id | bigint | NO |  |
| period_type | character varying(30) | NO |  |
| period_start | date | NO |  |
| period_end | date | NO |  |
| revenue_vnd | bigint | NO | 0 |
| order_count | integer | NO | 0 |
| quantity_sold | integer | NO | 0 |
| calculated_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ecommerce.cart_items

| column | type | null | default |
|---|---|---|---|
| cart_item_id | bigint | NO |  |
| cart_id | bigint | NO |  |
| product_id | bigint | NO |  |
| quantity | integer | NO |  |
| unit_price_vnd | bigint | NO |  |

### ecommerce.carts

| column | type | null | default |
|---|---|---|---|
| cart_id | bigint | NO |  |
| user_id | bigint | NO |  |
| status | character varying(30) | NO | 'active'::character varying |

### ecommerce.categories

| column | type | null | default |
|---|---|---|---|
| category_id | bigint | NO |  |
| name | character varying(255) | NO |  |
| parent_category_id | bigint | YES |  |

### ecommerce.materials

| column | type | null | default |
|---|---|---|---|
| material_id | bigint | NO |  |
| name | character varying(100) | NO |  |

### ecommerce.order_items

| column | type | null | default |
|---|---|---|---|
| order_item_id | bigint | NO |  |
| order_id | bigint | NO |  |
| product_id | bigint | NO |  |
| quantity | integer | NO |  |
| unit_price_vnd | bigint | NO |  |

### ecommerce.orders

| column | type | null | default |
|---|---|---|---|
| order_id | bigint | NO |  |
| user_id | bigint | NO |  |
| status | character varying(30) | NO |  |
| total_amount_vnd | bigint | NO |  |
| shipping_address | text | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |
| completed_at | timestamp without time zone | YES |  |

### ecommerce.product_categories

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| category_id | bigint | NO |  |
| is_primary | boolean | NO | false |

### ecommerce.product_dimensions

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| width_cm | numeric | NO |  |
| depth_cm | numeric | NO |  |
| height_cm | numeric | NO |  |

### ecommerce.product_images

| column | type | null | default |
|---|---|---|---|
| image_id | bigint | NO |  |
| product_id | bigint | NO |  |
| image_url | text | YES |  |
| local_path | text | YES |  |
| image_type | character varying(50) | YES |  |
| is_primary | boolean | NO | true |

### ecommerce.product_materials

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| material_id | bigint | NO |  |

### ecommerce.product_models

| column | type | null | default |
|---|---|---|---|
| model_id | bigint | NO |  |
| product_id | bigint | NO |  |
| model_url | text | YES |  |
| local_path | text | YES |  |
| format | character varying(30) | YES |  |
| scale | numeric | YES |  |
| status | character varying(30) | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ecommerce.product_space_types

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| space_type_id | bigint | NO |  |

### ecommerce.product_styles

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| style_id | bigint | NO |  |

### ecommerce.products

| column | type | null | default |
|---|---|---|---|
| product_id | bigint | NO |  |
| name | character varying(255) | NO |  |
| sku | character varying(100) | YES |  |
| description | text | YES |  |
| price_vnd | bigint | NO |  |
| stock_quantity | integer | NO | 0 |
| status | character varying(30) | NO |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ecommerce.reviews

| column | type | null | default |
|---|---|---|---|
| review_id | bigint | NO |  |
| user_id | bigint | NO |  |
| product_id | bigint | NO |  |
| rating | integer | NO |  |
| comment | text | YES |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### ecommerce.space_types

| column | type | null | default |
|---|---|---|---|
| space_type_id | bigint | NO |  |
| name | character varying(100) | NO |  |

### ecommerce.styles

| column | type | null | default |
|---|---|---|---|
| style_id | bigint | NO |  |
| code | character varying(50) | NO |  |
| name | character varying(100) | NO |  |

### ecommerce.users

| column | type | null | default |
|---|---|---|---|
| user_id | bigint | NO |  |
| full_name | character varying(255) | NO |  |
| email | character varying(255) | NO |  |
| password_hash | text | NO |  |
| phone | character varying(30) | YES |  |
| role | character varying(30) | NO | 'customer'::character varying |
| status | character varying(30) | NO | 'active'::character varying |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### public.alembic_version

| column | type | null | default |
|---|---|---|---|
| version_num | character varying(32) | NO |  |

### public.categories

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('categories_id_seq'::regclass) |
| name | character varying(120) | NO |  |
| slug | character varying(140) | NO |  |
| description | text | YES |  |
| parent_id | integer | YES |  |
| display_order | integer | NO | 0 |
| is_active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### public.product_attributes

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('product_attributes_id_seq'::regclass) |
| product_id | integer | NO |  |
| attribute_type | character varying(20) | NO |  |
| value | character varying(100) | NO |  |

### public.product_dimensions

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('product_dimensions_id_seq'::regclass) |
| product_id | integer | NO |  |
| length_cm | numeric | NO |  |
| width_cm | numeric | NO |  |
| height_cm | numeric | NO |  |

### public.product_images

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('product_images_id_seq'::regclass) |
| product_id | integer | NO |  |
| url | character varying(1024) | NO |  |
| alt_text | character varying(255) | YES |  |
| image_type | character varying(20) | NO | 'GALLERY'::character varying |
| is_primary | boolean | NO | false |
| display_order | integer | NO | 0 |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### public.product_models

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('product_models_id_seq'::regclass) |
| product_id | integer | NO |  |
| glb_url | character varying(1024) | NO |  |
| usdz_url | character varying(1024) | YES |  |
| file_size_bytes | bigint | YES |  |
| is_active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### public.products

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('products_id_seq'::regclass) |
| sku | character varying(64) | NO |  |
| name | character varying(255) | NO |  |
| description | text | YES |  |
| price | numeric | NO |  |
| currency | character varying(3) | NO | 'VND'::character varying |
| stock_quantity | integer | NO | 0 |
| status | character varying(20) | NO | 'ACTIVE'::character varying |
| category_id | integer | NO |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### public.users

| column | type | null | default |
|---|---|---|---|
| id | integer | NO | nextval('users_id_seq'::regclass) |
| email | character varying(255) | NO |  |
| password_hash | character varying(255) | NO |  |
| full_name | character varying(255) | NO |  |
| phone | character varying(20) | YES |  |
| shipping_address | text | YES |  |
| role | character varying(20) | NO | 'CUSTOMER'::character varying |
| is_active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### spatial.space_images

| column | type | null | default |
|---|---|---|---|
| image_id | bigint | NO |  |
| space_id | bigint | NO |  |
| image_url | text | YES |  |
| local_path | text | YES |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

### spatial.space_objects

| column | type | null | default |
|---|---|---|---|
| object_id | bigint | NO |  |
| space_id | bigint | NO |  |
| object_type | character varying(100) | NO |  |
| width_cm | numeric | YES |  |
| depth_cm | numeric | YES |  |
| height_cm | numeric | YES |  |
| position_x | numeric | YES |  |
| position_y | numeric | YES |  |
| position_z | numeric | YES |  |

### spatial.spaces

| column | type | null | default |
|---|---|---|---|
| space_id | bigint | NO |  |
| user_id | bigint | NO |  |
| space_type_id | bigint | NO |  |
| width_cm | numeric | NO |  |
| length_cm | numeric | NO |  |
| height_cm | numeric | NO |  |

### spatial.spatial_validations

| column | type | null | default |
|---|---|---|---|
| validation_id | bigint | NO |  |
| space_id | bigint | NO |  |
| product_id | bigint | NO |  |
| result_status | character varying(30) | NO |  |
| validation_details | jsonb | YES |  |
| created_at | timestamp without time zone | NO | CURRENT_TIMESTAMP |

## Constraints

- `ai.interactions` **interactions_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ai.interactions` **interactions_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `ai.interactions` **interactions_created_at_not_null**: NOT NULL created_at
- `ai.interactions` **interactions_interaction_id_not_null**: NOT NULL interaction_id
- `ai.interactions` **interactions_interaction_type_not_null**: NOT NULL interaction_type
- `ai.interactions` **interactions_product_id_not_null**: NOT NULL product_id
- `ai.interactions` **interactions_user_id_not_null**: NOT NULL user_id
- `ai.interactions` **interactions_pkey**: PRIMARY KEY (interaction_id)
- `ai.product_embeddings` **product_embeddings_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ai.product_embeddings` **product_embeddings_created_at_not_null**: NOT NULL created_at
- `ai.product_embeddings` **product_embeddings_embedding_id_not_null**: NOT NULL embedding_id
- `ai.product_embeddings` **product_embeddings_embedding_not_null**: NOT NULL embedding
- `ai.product_embeddings` **product_embeddings_embedding_type_not_null**: NOT NULL embedding_type
- `ai.product_embeddings` **product_embeddings_model_name_not_null**: NOT NULL model_name
- `ai.product_embeddings` **product_embeddings_product_id_not_null**: NOT NULL product_id
- `ai.product_embeddings` **product_embeddings_pkey**: PRIMARY KEY (embedding_id)
- `ai.recommendations` **recommendations_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ai.recommendations` **recommendations_space_id_fkey**: FOREIGN KEY (space_id) REFERENCES spatial.spaces(space_id) ON DELETE SET NULL
- `ai.recommendations` **recommendations_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `ai.recommendations` **recommendations_created_at_not_null**: NOT NULL created_at
- `ai.recommendations` **recommendations_product_id_not_null**: NOT NULL product_id
- `ai.recommendations` **recommendations_recommendation_id_not_null**: NOT NULL recommendation_id
- `ai.recommendations` **recommendations_user_id_not_null**: NOT NULL user_id
- `ai.recommendations` **recommendations_pkey**: PRIMARY KEY (recommendation_id)
- `ai.space_embeddings` **space_embeddings_image_id_fkey**: FOREIGN KEY (image_id) REFERENCES spatial.space_images(image_id) ON DELETE CASCADE
- `ai.space_embeddings` **space_embeddings_created_at_not_null**: NOT NULL created_at
- `ai.space_embeddings` **space_embeddings_embedding_id_not_null**: NOT NULL embedding_id
- `ai.space_embeddings` **space_embeddings_embedding_not_null**: NOT NULL embedding
- `ai.space_embeddings` **space_embeddings_embedding_type_not_null**: NOT NULL embedding_type
- `ai.space_embeddings` **space_embeddings_image_id_not_null**: NOT NULL image_id
- `ai.space_embeddings` **space_embeddings_model_name_not_null**: NOT NULL model_name
- `ai.space_embeddings` **space_embeddings_pkey**: PRIMARY KEY (embedding_id)
- `ai.user_preferences` **user_preferences_category_id_fkey**: FOREIGN KEY (category_id) REFERENCES ecommerce.categories(category_id) ON DELETE SET NULL
- `ai.user_preferences` **user_preferences_material_id_fkey**: FOREIGN KEY (material_id) REFERENCES ecommerce.materials(material_id) ON DELETE SET NULL
- `ai.user_preferences` **user_preferences_style_id_fkey**: FOREIGN KEY (style_id) REFERENCES ecommerce.styles(style_id) ON DELETE SET NULL
- `ai.user_preferences` **user_preferences_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `ai.user_preferences` **user_preferences_preference_id_not_null**: NOT NULL preference_id
- `ai.user_preferences` **user_preferences_user_id_not_null**: NOT NULL user_id
- `ai.user_preferences` **user_preferences_pkey**: PRIMARY KEY (preference_id)
- `analytics.sales_kpi_summaries` **chk_kpi_order_count**: CHECK ((order_count >= 0))
- `analytics.sales_kpi_summaries` **chk_kpi_period**: CHECK ((period_end >= period_start))
- `analytics.sales_kpi_summaries` **chk_kpi_quantity**: CHECK ((quantity_sold >= 0))
- `analytics.sales_kpi_summaries` **chk_kpi_revenue**: CHECK ((revenue_vnd >= 0))
- `analytics.sales_kpi_summaries` **chk_sales_kpi_period_type**: CHECK (((period_type)::text = ANY ((ARRAY['DAY'::character varying, 'MONTH'::character varying, 'QUARTER'::character varying, 'YEAR'::character varying])::text[])))
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_calculated_at_not_null**: NOT NULL calculated_at
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_kpi_id_not_null**: NOT NULL kpi_id
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_order_count_not_null**: NOT NULL order_count
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_period_end_not_null**: NOT NULL period_end
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_period_start_not_null**: NOT NULL period_start
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_period_type_not_null**: NOT NULL period_type
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_quantity_sold_not_null**: NOT NULL quantity_sold
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_revenue_vnd_not_null**: NOT NULL revenue_vnd
- `analytics.sales_kpi_summaries` **sales_kpi_summaries_pkey**: PRIMARY KEY (kpi_id)
- `analytics.sales_kpi_summaries` **uq_sales_kpi_period**: UNIQUE (period_type, period_start)
- `ecommerce.cart_items` **chk_cart_items_price**: CHECK ((unit_price_vnd >= 0))
- `ecommerce.cart_items` **chk_cart_items_quantity**: CHECK ((quantity > 0))
- `ecommerce.cart_items` **cart_items_cart_id_fkey**: FOREIGN KEY (cart_id) REFERENCES ecommerce.carts(cart_id) ON DELETE CASCADE
- `ecommerce.cart_items` **cart_items_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id)
- `ecommerce.cart_items` **cart_items_cart_id_not_null**: NOT NULL cart_id
- `ecommerce.cart_items` **cart_items_cart_item_id_not_null**: NOT NULL cart_item_id
- `ecommerce.cart_items` **cart_items_product_id_not_null**: NOT NULL product_id
- `ecommerce.cart_items` **cart_items_quantity_not_null**: NOT NULL quantity
- `ecommerce.cart_items` **cart_items_unit_price_vnd_not_null**: NOT NULL unit_price_vnd
- `ecommerce.cart_items` **cart_items_pkey**: PRIMARY KEY (cart_item_id)
- `ecommerce.cart_items` **uq_cart_product**: UNIQUE (cart_id, product_id)
- `ecommerce.carts` **carts_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `ecommerce.carts` **carts_cart_id_not_null**: NOT NULL cart_id
- `ecommerce.carts` **carts_status_not_null**: NOT NULL status
- `ecommerce.carts` **carts_user_id_not_null**: NOT NULL user_id
- `ecommerce.carts` **carts_pkey**: PRIMARY KEY (cart_id)
- `ecommerce.carts` **carts_user_id_key**: UNIQUE (user_id)
- `ecommerce.categories` **categories_parent_category_id_fkey**: FOREIGN KEY (parent_category_id) REFERENCES ecommerce.categories(category_id)
- `ecommerce.categories` **categories_category_id_not_null**: NOT NULL category_id
- `ecommerce.categories` **categories_name_not_null**: NOT NULL name
- `ecommerce.categories` **categories_pkey**: PRIMARY KEY (category_id)
- `ecommerce.materials` **materials_material_id_not_null**: NOT NULL material_id
- `ecommerce.materials` **materials_name_not_null**: NOT NULL name
- `ecommerce.materials` **materials_pkey**: PRIMARY KEY (material_id)
- `ecommerce.materials` **materials_name_key**: UNIQUE (name)
- `ecommerce.order_items` **chk_order_items_price**: CHECK ((unit_price_vnd >= 0))
- `ecommerce.order_items` **chk_order_items_quantity**: CHECK ((quantity > 0))
- `ecommerce.order_items` **order_items_order_id_fkey**: FOREIGN KEY (order_id) REFERENCES ecommerce.orders(order_id) ON DELETE CASCADE
- `ecommerce.order_items` **order_items_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id)
- `ecommerce.order_items` **order_items_order_id_not_null**: NOT NULL order_id
- `ecommerce.order_items` **order_items_order_item_id_not_null**: NOT NULL order_item_id
- `ecommerce.order_items` **order_items_product_id_not_null**: NOT NULL product_id
- `ecommerce.order_items` **order_items_quantity_not_null**: NOT NULL quantity
- `ecommerce.order_items` **order_items_unit_price_vnd_not_null**: NOT NULL unit_price_vnd
- `ecommerce.order_items` **order_items_pkey**: PRIMARY KEY (order_item_id)
- `ecommerce.order_items` **uq_order_product**: UNIQUE (order_id, product_id)
- `ecommerce.orders` **chk_orders_total**: CHECK ((total_amount_vnd >= 0))
- `ecommerce.orders` **orders_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id)
- `ecommerce.orders` **orders_created_at_not_null**: NOT NULL created_at
- `ecommerce.orders` **orders_order_id_not_null**: NOT NULL order_id
- `ecommerce.orders` **orders_shipping_address_not_null**: NOT NULL shipping_address
- `ecommerce.orders` **orders_status_not_null**: NOT NULL status
- `ecommerce.orders` **orders_total_amount_vnd_not_null**: NOT NULL total_amount_vnd
- `ecommerce.orders` **orders_user_id_not_null**: NOT NULL user_id
- `ecommerce.orders` **orders_pkey**: PRIMARY KEY (order_id)
- `ecommerce.product_categories` **product_categories_category_id_fkey**: FOREIGN KEY (category_id) REFERENCES ecommerce.categories(category_id) ON DELETE CASCADE
- `ecommerce.product_categories` **product_categories_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_categories` **product_categories_category_id_not_null**: NOT NULL category_id
- `ecommerce.product_categories` **product_categories_is_primary_not_null**: NOT NULL is_primary
- `ecommerce.product_categories` **product_categories_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_categories` **product_categories_pkey**: PRIMARY KEY (product_id, category_id)
- `ecommerce.product_dimensions` **chk_product_dimensions_depth**: CHECK ((depth_cm > (0)::numeric))
- `ecommerce.product_dimensions` **chk_product_dimensions_height**: CHECK ((height_cm > (0)::numeric))
- `ecommerce.product_dimensions` **chk_product_dimensions_width**: CHECK ((width_cm > (0)::numeric))
- `ecommerce.product_dimensions` **product_dimensions_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_dimensions` **product_dimensions_depth_cm_not_null**: NOT NULL depth_cm
- `ecommerce.product_dimensions` **product_dimensions_height_cm_not_null**: NOT NULL height_cm
- `ecommerce.product_dimensions` **product_dimensions_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_dimensions` **product_dimensions_width_cm_not_null**: NOT NULL width_cm
- `ecommerce.product_dimensions` **product_dimensions_pkey**: PRIMARY KEY (product_id)
- `ecommerce.product_images` **product_images_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_images` **product_images_image_id_not_null**: NOT NULL image_id
- `ecommerce.product_images` **product_images_is_primary_not_null**: NOT NULL is_primary
- `ecommerce.product_images` **product_images_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_images` **product_images_pkey**: PRIMARY KEY (image_id)
- `ecommerce.product_images` **product_images_product_id_key**: UNIQUE (product_id)
- `ecommerce.product_materials` **product_materials_material_id_fkey**: FOREIGN KEY (material_id) REFERENCES ecommerce.materials(material_id) ON DELETE CASCADE
- `ecommerce.product_materials` **product_materials_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_materials` **product_materials_material_id_not_null**: NOT NULL material_id
- `ecommerce.product_materials` **product_materials_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_materials` **product_materials_pkey**: PRIMARY KEY (product_id, material_id)
- `ecommerce.product_models` **product_models_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_models` **product_models_created_at_not_null**: NOT NULL created_at
- `ecommerce.product_models` **product_models_model_id_not_null**: NOT NULL model_id
- `ecommerce.product_models` **product_models_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_models` **product_models_status_not_null**: NOT NULL status
- `ecommerce.product_models` **product_models_updated_at_not_null**: NOT NULL updated_at
- `ecommerce.product_models` **product_models_pkey**: PRIMARY KEY (model_id)
- `ecommerce.product_models` **product_models_product_id_key**: UNIQUE (product_id)
- `ecommerce.product_space_types` **product_space_types_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_space_types` **product_space_types_space_type_id_fkey**: FOREIGN KEY (space_type_id) REFERENCES ecommerce.space_types(space_type_id) ON DELETE CASCADE
- `ecommerce.product_space_types` **product_space_types_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_space_types` **product_space_types_space_type_id_not_null**: NOT NULL space_type_id
- `ecommerce.product_space_types` **product_space_types_pkey**: PRIMARY KEY (product_id, space_type_id)
- `ecommerce.product_styles` **product_styles_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.product_styles` **product_styles_style_id_fkey**: FOREIGN KEY (style_id) REFERENCES ecommerce.styles(style_id) ON DELETE CASCADE
- `ecommerce.product_styles` **product_styles_product_id_not_null**: NOT NULL product_id
- `ecommerce.product_styles` **product_styles_style_id_not_null**: NOT NULL style_id
- `ecommerce.product_styles` **product_styles_pkey**: PRIMARY KEY (product_id, style_id)
- `ecommerce.products` **chk_products_price**: CHECK ((price_vnd >= 0))
- `ecommerce.products` **chk_products_stock**: CHECK ((stock_quantity >= 0))
- `ecommerce.products` **products_created_at_not_null**: NOT NULL created_at
- `ecommerce.products` **products_name_not_null**: NOT NULL name
- `ecommerce.products` **products_price_vnd_not_null**: NOT NULL price_vnd
- `ecommerce.products` **products_product_id_not_null**: NOT NULL product_id
- `ecommerce.products` **products_status_not_null**: NOT NULL status
- `ecommerce.products` **products_stock_quantity_not_null**: NOT NULL stock_quantity
- `ecommerce.products` **products_updated_at_not_null**: NOT NULL updated_at
- `ecommerce.products` **products_pkey**: PRIMARY KEY (product_id)
- `ecommerce.products` **products_sku_key**: UNIQUE (sku)
- `ecommerce.reviews` **chk_reviews_rating**: CHECK (((rating >= 1) AND (rating <= 5)))
- `ecommerce.reviews` **reviews_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `ecommerce.reviews` **reviews_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `ecommerce.reviews` **reviews_created_at_not_null**: NOT NULL created_at
- `ecommerce.reviews` **reviews_product_id_not_null**: NOT NULL product_id
- `ecommerce.reviews` **reviews_rating_not_null**: NOT NULL rating
- `ecommerce.reviews` **reviews_review_id_not_null**: NOT NULL review_id
- `ecommerce.reviews` **reviews_user_id_not_null**: NOT NULL user_id
- `ecommerce.reviews` **reviews_pkey**: PRIMARY KEY (review_id)
- `ecommerce.reviews` **uq_user_product_review**: UNIQUE (user_id, product_id)
- `ecommerce.space_types` **space_types_name_not_null**: NOT NULL name
- `ecommerce.space_types` **space_types_space_type_id_not_null**: NOT NULL space_type_id
- `ecommerce.space_types` **space_types_pkey**: PRIMARY KEY (space_type_id)
- `ecommerce.space_types` **space_types_name_key**: UNIQUE (name)
- `ecommerce.styles` **styles_code_not_null**: NOT NULL code
- `ecommerce.styles` **styles_name_not_null**: NOT NULL name
- `ecommerce.styles` **styles_style_id_not_null**: NOT NULL style_id
- `ecommerce.styles` **styles_pkey**: PRIMARY KEY (style_id)
- `ecommerce.styles` **styles_code_key**: UNIQUE (code)
- `ecommerce.users` **users_created_at_not_null**: NOT NULL created_at
- `ecommerce.users` **users_email_not_null**: NOT NULL email
- `ecommerce.users` **users_full_name_not_null**: NOT NULL full_name
- `ecommerce.users` **users_password_hash_not_null**: NOT NULL password_hash
- `ecommerce.users` **users_role_not_null**: NOT NULL role
- `ecommerce.users` **users_status_not_null**: NOT NULL status
- `ecommerce.users` **users_updated_at_not_null**: NOT NULL updated_at
- `ecommerce.users` **users_user_id_not_null**: NOT NULL user_id
- `ecommerce.users` **users_pkey**: PRIMARY KEY (user_id)
- `ecommerce.users` **users_email_key**: UNIQUE (email)
- `public.alembic_version` **alembic_version_version_num_not_null**: NOT NULL version_num
- `public.alembic_version` **alembic_version_pkc**: PRIMARY KEY (version_num)
- `public.categories` **fk_categories_parent_id_categories**: FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE RESTRICT
- `public.categories` **categories_created_at_not_null**: NOT NULL created_at
- `public.categories` **categories_display_order_not_null**: NOT NULL display_order
- `public.categories` **categories_id_not_null**: NOT NULL id
- `public.categories` **categories_is_active_not_null**: NOT NULL is_active
- `public.categories` **categories_name_not_null**: NOT NULL name
- `public.categories` **categories_slug_not_null**: NOT NULL slug
- `public.categories` **categories_updated_at_not_null**: NOT NULL updated_at
- `public.categories` **pk_categories**: PRIMARY KEY (id)
- `public.categories` **uq_categories_name**: UNIQUE (name)
- `public.product_attributes` **ck_product_attributes_attribute_type**: CHECK (((attribute_type)::text = ANY ((ARRAY['MATERIAL'::character varying, 'STYLE'::character varying, 'COLOR'::character varying])::text[])))
- `public.product_attributes` **fk_product_attributes_product_id_products**: FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
- `public.product_attributes` **product_attributes_attribute_type_not_null**: NOT NULL attribute_type
- `public.product_attributes` **product_attributes_id_not_null**: NOT NULL id
- `public.product_attributes` **product_attributes_product_id_not_null**: NOT NULL product_id
- `public.product_attributes` **product_attributes_value_not_null**: NOT NULL value
- `public.product_attributes` **pk_product_attributes**: PRIMARY KEY (id)
- `public.product_attributes` **uq_product_attr**: UNIQUE (product_id, attribute_type, value)
- `public.product_dimensions` **ck_product_dimensions_height_positive**: CHECK ((height_cm > (0)::numeric))
- `public.product_dimensions` **ck_product_dimensions_length_positive**: CHECK ((length_cm > (0)::numeric))
- `public.product_dimensions` **ck_product_dimensions_width_positive**: CHECK ((width_cm > (0)::numeric))
- `public.product_dimensions` **fk_product_dimensions_product_id_products**: FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
- `public.product_dimensions` **product_dimensions_height_cm_not_null**: NOT NULL height_cm
- `public.product_dimensions` **product_dimensions_id_not_null**: NOT NULL id
- `public.product_dimensions` **product_dimensions_length_cm_not_null**: NOT NULL length_cm
- `public.product_dimensions` **product_dimensions_product_id_not_null**: NOT NULL product_id
- `public.product_dimensions` **product_dimensions_width_cm_not_null**: NOT NULL width_cm
- `public.product_dimensions` **pk_product_dimensions**: PRIMARY KEY (id)
- `public.product_dimensions` **uq_product_dimensions_product_id**: UNIQUE (product_id)
- `public.product_images` **ck_product_images_image_type**: CHECK (((image_type)::text = ANY ((ARRAY['GALLERY'::character varying, 'VIEW_360'::character varying])::text[])))
- `public.product_images` **fk_product_images_product_id_products**: FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
- `public.product_images` **product_images_created_at_not_null**: NOT NULL created_at
- `public.product_images` **product_images_display_order_not_null**: NOT NULL display_order
- `public.product_images` **product_images_id_not_null**: NOT NULL id
- `public.product_images` **product_images_image_type_not_null**: NOT NULL image_type
- `public.product_images` **product_images_is_primary_not_null**: NOT NULL is_primary
- `public.product_images` **product_images_product_id_not_null**: NOT NULL product_id
- `public.product_images` **product_images_updated_at_not_null**: NOT NULL updated_at
- `public.product_images` **product_images_url_not_null**: NOT NULL url
- `public.product_images` **pk_product_images**: PRIMARY KEY (id)
- `public.product_models` **ck_product_models_glb_size_limit**: CHECK (((file_size_bytes IS NULL) OR (file_size_bytes <= 15728640)))
- `public.product_models` **fk_product_models_product_id_products**: FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
- `public.product_models` **product_models_created_at_not_null**: NOT NULL created_at
- `public.product_models` **product_models_glb_url_not_null**: NOT NULL glb_url
- `public.product_models` **product_models_id_not_null**: NOT NULL id
- `public.product_models` **product_models_is_active_not_null**: NOT NULL is_active
- `public.product_models` **product_models_product_id_not_null**: NOT NULL product_id
- `public.product_models` **product_models_updated_at_not_null**: NOT NULL updated_at
- `public.product_models` **pk_product_models**: PRIMARY KEY (id)
- `public.products` **ck_products_price_positive**: CHECK ((price > (0)::numeric))
- `public.products` **ck_products_product_status**: CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'INACTIVE'::character varying])::text[])))
- `public.products` **ck_products_stock_non_negative**: CHECK ((stock_quantity >= 0))
- `public.products` **fk_products_category_id_categories**: FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
- `public.products` **products_category_id_not_null**: NOT NULL category_id
- `public.products` **products_created_at_not_null**: NOT NULL created_at
- `public.products` **products_currency_not_null**: NOT NULL currency
- `public.products` **products_id_not_null**: NOT NULL id
- `public.products` **products_name_not_null**: NOT NULL name
- `public.products` **products_price_not_null**: NOT NULL price
- `public.products` **products_sku_not_null**: NOT NULL sku
- `public.products` **products_status_not_null**: NOT NULL status
- `public.products` **products_stock_quantity_not_null**: NOT NULL stock_quantity
- `public.products` **products_updated_at_not_null**: NOT NULL updated_at
- `public.products` **pk_products**: PRIMARY KEY (id)
- `public.users` **ck_users_user_role**: CHECK (((role)::text = ANY ((ARRAY['CUSTOMER'::character varying, 'STORE_MANAGER'::character varying])::text[])))
- `public.users` **users_created_at_not_null**: NOT NULL created_at
- `public.users` **users_email_not_null**: NOT NULL email
- `public.users` **users_full_name_not_null**: NOT NULL full_name
- `public.users` **users_id_not_null**: NOT NULL id
- `public.users` **users_is_active_not_null**: NOT NULL is_active
- `public.users` **users_password_hash_not_null**: NOT NULL password_hash
- `public.users` **users_role_not_null**: NOT NULL role
- `public.users` **users_updated_at_not_null**: NOT NULL updated_at
- `public.users` **pk_users**: PRIMARY KEY (id)
- `spatial.space_images` **space_images_space_id_fkey**: FOREIGN KEY (space_id) REFERENCES spatial.spaces(space_id) ON DELETE CASCADE
- `spatial.space_images` **space_images_created_at_not_null**: NOT NULL created_at
- `spatial.space_images` **space_images_image_id_not_null**: NOT NULL image_id
- `spatial.space_images` **space_images_space_id_not_null**: NOT NULL space_id
- `spatial.space_images` **space_images_pkey**: PRIMARY KEY (image_id)
- `spatial.space_objects` **space_objects_space_id_fkey**: FOREIGN KEY (space_id) REFERENCES spatial.spaces(space_id) ON DELETE CASCADE
- `spatial.space_objects` **space_objects_object_id_not_null**: NOT NULL object_id
- `spatial.space_objects` **space_objects_object_type_not_null**: NOT NULL object_type
- `spatial.space_objects` **space_objects_space_id_not_null**: NOT NULL space_id
- `spatial.space_objects` **space_objects_pkey**: PRIMARY KEY (object_id)
- `spatial.spaces` **chk_spaces_height**: CHECK ((height_cm > (0)::numeric))
- `spatial.spaces` **chk_spaces_length**: CHECK ((length_cm > (0)::numeric))
- `spatial.spaces` **chk_spaces_width**: CHECK ((width_cm > (0)::numeric))
- `spatial.spaces` **spaces_space_type_id_fkey**: FOREIGN KEY (space_type_id) REFERENCES ecommerce.space_types(space_type_id)
- `spatial.spaces` **spaces_user_id_fkey**: FOREIGN KEY (user_id) REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
- `spatial.spaces` **spaces_height_cm_not_null**: NOT NULL height_cm
- `spatial.spaces` **spaces_length_cm_not_null**: NOT NULL length_cm
- `spatial.spaces` **spaces_space_id_not_null**: NOT NULL space_id
- `spatial.spaces` **spaces_space_type_id_not_null**: NOT NULL space_type_id
- `spatial.spaces` **spaces_user_id_not_null**: NOT NULL user_id
- `spatial.spaces` **spaces_width_cm_not_null**: NOT NULL width_cm
- `spatial.spaces` **spaces_pkey**: PRIMARY KEY (space_id)
- `spatial.spatial_validations` **spatial_validations_product_id_fkey**: FOREIGN KEY (product_id) REFERENCES ecommerce.products(product_id) ON DELETE CASCADE
- `spatial.spatial_validations` **spatial_validations_space_id_fkey**: FOREIGN KEY (space_id) REFERENCES spatial.spaces(space_id) ON DELETE CASCADE
- `spatial.spatial_validations` **spatial_validations_created_at_not_null**: NOT NULL created_at
- `spatial.spatial_validations` **spatial_validations_product_id_not_null**: NOT NULL product_id
- `spatial.spatial_validations` **spatial_validations_result_status_not_null**: NOT NULL result_status
- `spatial.spatial_validations` **spatial_validations_space_id_not_null**: NOT NULL space_id
- `spatial.spatial_validations` **spatial_validations_validation_id_not_null**: NOT NULL validation_id
- `spatial.spatial_validations` **spatial_validations_pkey**: PRIMARY KEY (validation_id)

## Indexes

- CREATE UNIQUE INDEX interactions_pkey ON ai.interactions USING btree (interaction_id)
- CREATE UNIQUE INDEX product_embeddings_pkey ON ai.product_embeddings USING btree (embedding_id)
- CREATE UNIQUE INDEX recommendations_pkey ON ai.recommendations USING btree (recommendation_id)
- CREATE UNIQUE INDEX space_embeddings_pkey ON ai.space_embeddings USING btree (embedding_id)
- CREATE UNIQUE INDEX user_preferences_pkey ON ai.user_preferences USING btree (preference_id)
- CREATE UNIQUE INDEX sales_kpi_summaries_pkey ON analytics.sales_kpi_summaries USING btree (kpi_id)
- CREATE UNIQUE INDEX uq_sales_kpi_period ON analytics.sales_kpi_summaries USING btree (period_type, period_start)
- CREATE UNIQUE INDEX cart_items_pkey ON ecommerce.cart_items USING btree (cart_item_id)
- CREATE UNIQUE INDEX uq_cart_product ON ecommerce.cart_items USING btree (cart_id, product_id)
- CREATE UNIQUE INDEX carts_pkey ON ecommerce.carts USING btree (cart_id)
- CREATE UNIQUE INDEX carts_user_id_key ON ecommerce.carts USING btree (user_id)
- CREATE UNIQUE INDEX categories_pkey ON ecommerce.categories USING btree (category_id)
- CREATE UNIQUE INDEX materials_name_key ON ecommerce.materials USING btree (name)
- CREATE UNIQUE INDEX materials_pkey ON ecommerce.materials USING btree (material_id)
- CREATE UNIQUE INDEX order_items_pkey ON ecommerce.order_items USING btree (order_item_id)
- CREATE UNIQUE INDEX uq_order_product ON ecommerce.order_items USING btree (order_id, product_id)
- CREATE UNIQUE INDEX orders_pkey ON ecommerce.orders USING btree (order_id)
- CREATE UNIQUE INDEX product_categories_pkey ON ecommerce.product_categories USING btree (product_id, category_id)
- CREATE UNIQUE INDEX uq_product_one_primary_category ON ecommerce.product_categories USING btree (product_id) WHERE (is_primary = true)
- CREATE UNIQUE INDEX product_dimensions_pkey ON ecommerce.product_dimensions USING btree (product_id)
- CREATE UNIQUE INDEX product_images_pkey ON ecommerce.product_images USING btree (image_id)
- CREATE UNIQUE INDEX product_images_product_id_key ON ecommerce.product_images USING btree (product_id)
- CREATE UNIQUE INDEX product_materials_pkey ON ecommerce.product_materials USING btree (product_id, material_id)
- CREATE UNIQUE INDEX product_models_pkey ON ecommerce.product_models USING btree (model_id)
- CREATE UNIQUE INDEX product_models_product_id_key ON ecommerce.product_models USING btree (product_id)
- CREATE UNIQUE INDEX product_space_types_pkey ON ecommerce.product_space_types USING btree (product_id, space_type_id)
- CREATE UNIQUE INDEX product_styles_pkey ON ecommerce.product_styles USING btree (product_id, style_id)
- CREATE UNIQUE INDEX products_pkey ON ecommerce.products USING btree (product_id)
- CREATE UNIQUE INDEX products_sku_key ON ecommerce.products USING btree (sku)
- CREATE UNIQUE INDEX reviews_pkey ON ecommerce.reviews USING btree (review_id)
- CREATE UNIQUE INDEX uq_user_product_review ON ecommerce.reviews USING btree (user_id, product_id)
- CREATE UNIQUE INDEX space_types_name_key ON ecommerce.space_types USING btree (name)
- CREATE UNIQUE INDEX space_types_pkey ON ecommerce.space_types USING btree (space_type_id)
- CREATE UNIQUE INDEX styles_code_key ON ecommerce.styles USING btree (code)
- CREATE UNIQUE INDEX styles_pkey ON ecommerce.styles USING btree (style_id)
- CREATE UNIQUE INDEX users_email_key ON ecommerce.users USING btree (email)
- CREATE UNIQUE INDEX users_pkey ON ecommerce.users USING btree (user_id)
- CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num)
- CREATE INDEX ix_categories_parent_id ON public.categories USING btree (parent_id)
- CREATE UNIQUE INDEX ix_categories_slug ON public.categories USING btree (slug)
- CREATE UNIQUE INDEX pk_categories ON public.categories USING btree (id)
- CREATE UNIQUE INDEX uq_categories_name ON public.categories USING btree (name)
- CREATE INDEX ix_product_attributes_product_id ON public.product_attributes USING btree (product_id)
- CREATE INDEX ix_product_attributes_type_value ON public.product_attributes USING btree (attribute_type, value)
- CREATE UNIQUE INDEX pk_product_attributes ON public.product_attributes USING btree (id)
- CREATE UNIQUE INDEX uq_product_attr ON public.product_attributes USING btree (product_id, attribute_type, value)
- CREATE UNIQUE INDEX pk_product_dimensions ON public.product_dimensions USING btree (id)
- CREATE UNIQUE INDEX uq_product_dimensions_product_id ON public.product_dimensions USING btree (product_id)
- CREATE INDEX ix_product_images_product_id ON public.product_images USING btree (product_id)
- CREATE UNIQUE INDEX pk_product_images ON public.product_images USING btree (id)
- CREATE INDEX ix_product_models_product_id ON public.product_models USING btree (product_id)
- CREATE UNIQUE INDEX pk_product_models ON public.product_models USING btree (id)
- CREATE INDEX ix_products_category_status ON public.products USING btree (category_id, status)
- CREATE INDEX ix_products_name ON public.products USING btree (name)
- CREATE UNIQUE INDEX ix_products_sku ON public.products USING btree (sku)
- CREATE INDEX ix_products_status ON public.products USING btree (status)
- CREATE UNIQUE INDEX pk_products ON public.products USING btree (id)
- CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email)
- CREATE UNIQUE INDEX pk_users ON public.users USING btree (id)
- CREATE UNIQUE INDEX space_images_pkey ON spatial.space_images USING btree (image_id)
- CREATE UNIQUE INDEX space_objects_pkey ON spatial.space_objects USING btree (object_id)
- CREATE UNIQUE INDEX spaces_pkey ON spatial.spaces USING btree (space_id)
- CREATE UNIQUE INDEX spatial_validations_pkey ON spatial.spatial_validations USING btree (validation_id)