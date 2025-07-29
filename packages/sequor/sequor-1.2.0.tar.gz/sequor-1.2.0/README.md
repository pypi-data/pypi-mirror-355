# Sequor
Sequor is a SQL-centric workflow platform for building reliable API integrations in modern data stacks. It's the open alternative to black-box SaaS connectors, giving data teams complete control over their integration pipelines.

Sequor fuses API execution with your database, enabling bidirectional data flow between APIs and database tables. By storing intermediate data in your database, you can leverage the full power of SQL for transformations, analytics, and business logic. This unified execution model eliminates the traditional boundary between iPaaS-style app integration and ETL-style data pipelines.

With Sequor's code-first approach (YAML for flows, Jinja or Python for dynamic parameters, and SQL for logic), you can apply software engineering best practices to integrations: version control, collaboration, CI/CD, and local development.

**Own**, **control**, and **scale** your integrations with transparent configuration, familiar open technologies, and without SaaS lock-in.

# How Sequor works
Sequor is designed around an intuitive YAML-based workflow definition. Every integration  flow is built from these powerful operations:

* **http_request** - Execute API calls with database integration that iterates over input records, performs dynamic HTTP requests, and maps responses back to database tables. Use Jinja templates or Python snippets for dynamic parameterization.
* **transform** - Apply SQL queries to prepare data for API calls or process API results, leveraging the full power of your database for data manipulation.
* **control statements** - Build robust workflows with if-then-else conditionals, while loops, try-catch error handling, and more. These high-level orchestration capabilities ensure your integrations handle edge cases gracefully without custom code.

## Example 1 - Data acquisition: Load BigCommerce customers into database
```yaml
- op: http_request
  request:
    source: "bigcommerce"
    url: "https://api.bigcommerce.com/stores/{{ var('store_hash') }}/{{ var('api_version') }}/customers"
    method: GET
    headers:
      "Accept": "application/json"
  response:
    success_status: [200]
    tables: 
      - source: "stage"
        table: "bc_customers"
        columns: {"id": "text", "first_name": "text", "last_name": "text"}
        data_expression: response.json()['data']
```

## Example 2 - Reverse ETL: Update Mailchimp custom fields with customer metrics from a database table
```yaml
- op: http_request
  for_each:
    source: "postgres"
    table: "customer_metrics"
    as: customer
  request:
    source: "mailchimp"
    url_expression: |
      email = context.var('customer')['email']
      import hashlib
      subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
      return "https://{{ var('dc') }}.api.mailchimp.com/{{ var('api_version') }}/lists/{{ var('mailchimp_list_id') }}/members/" + subscriber_hash
    method: PATCH
    body_format: json
    body_expression: |
      customer = var('customer')
      return {
        "merge_fields": {
          "TOTALSPENT": customer['total_spent'],
          "ORDERCOUNT": customer['order_count']
        }
      }
  response:
    success_status: [200]
```

## Example 3 - Complex data handling: Map nested Shopify data into referenced tables
```yaml
- op: http_request
  request:
    source: "shopify"
    url: "https://{{ var('store_name') }}.myshopify.com/admin/api/{{ var('api_version') }}/customers.json"
    method: GET
    headers:
      "Accept": "application/json"
  response:
    success_status: [200]
    tables: 
      - source: "postgres"
        table: "shopify_customers"
        columns: {
          "id": "text", "first_name": "text", "last_name": "text", "email": "text"
        }
        data_expression: |
          customers = response.json()['customers']          
          for customer in customers:            
            # flattening the nested object
            customer['email_consent_state'] = customer['email_marketing_consent'].get('state') 
            customer['opt_in_level'] = customer['email_marketing_consent'].get('single_opt_in')
          return customers
      - source: "postgres"
        table: "shopify_customer_addresses"
        columns: {
          "id": "text", "customer_id": "text", "address1": "text", "address2": "text",
          "city": "text", "province": "text", "zip": "text", "country": "text"
        }
        data_expression: |
          customers = response.json()['customers']          
          customer_addresses = []
          for customer in customers:              
            # extract nested list of addresses and add customer_id to each address for reference
            for address in customer['addresses']:
              address['customer_id'] = customer['id'] 
              customer_addresses.append(address)
          return customer_addresses
```

## Example 4: Run SQL to prepare API input, transform API responses, or build analytics table
```yaml
- op: transform
  source: postgres
  target_table: customer_order_analytics
  query: |
    SELECT
      c.id,
      c.name,
      c.email,
      o.count as order_count,
      o.total as lifetime_value
      FROM customers c
    LEFT JOIN (
      SELECT
          customer_id,
          COUNT(*) as count,
          SUM(amount) as total
      FROM orders
      GROUP BY customer_id
    ) o ON c.id = o.customer_id
    WHERE c.active = true;
```

## Example 5: Orchestrate complex worflows with procedural statements
```yaml
- op: if
  conditions:
    - condition_expression: query_scalar("postgres", "select count(*) from inventory_to_update") > 0
      then:
        - op: run_workflow
          flow: "update_inventory"
  else:
    - op: print
      message: "Inventory is up to date"
```


# Getting started
* [Install Sequor](https://docs.sequor.dev/getting-started/installation). It is easy to start with `pip install sequor`.
* [Follow Quickstart](https://docs.sequor.dev/getting-started/quickstart)
* [Explore examples of real-life integrations](https://github.com/paloaltodatabases/sequor-integrations)
* [Documentation](https://docs.sequor.dev/)

# Community
* [Discuss Sequor on GitHub](https://github.com/paloaltodatabases/sequor/discussions) - To get help and participate in discussions about best practices, or any other conversation that would benefit from being searchable

# Stay connected
* [Subsribe to our newsletter](https://buttondown.com/sequor) -  updated on new releases and features, guides, and case studies.






  
