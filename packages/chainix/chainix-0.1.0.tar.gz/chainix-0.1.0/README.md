# Chainix

A Python client library for executing chains with chainix.ai

## Installation

```bash
pip install chainix
```

## Quick Start

```python
from chainix import AsyncChainClient

# Initialize the client
client = AsyncChainClient(
    chain_id="your-chains-id-here",
    api_key="your-api-key-here",
)

# Define your custom functions
def refund(args):
    try:
        order_id = args['order id']
        print(f"Issuing a refund for order: {order_id}")
    
        # Your business logic here
        # ... process refund ...
        amount = 500
        
        return {
            'success': True,
            'vars_to_update': {
                'refund_amount': amount
            }
        }
    except Exception as e:
        print(f"Failed to process refund: {e}")
        return {
            'success': False,
            'vars_to_update': {}
        }


def cancel_order(args):
    try:
        order_id = args['order id']
        print(f"Cancelling order: {order_id}")
    
        # Your business logic here
        # ... perform cancellation ...
        
        return {
            'success': True,
            'vars_to_update': {}
        }
    except Exception as e:
        print(f"Failed to cancel order: {e}")
        return {
            'success': False,
            'vars_to_update': {}
        }


# Register your functions (use the actual function IDs from the chain on chainix.ai)
client.register_function("your-cancel-function-id", cancel_order)
client.register_function("your-refund-function-id", refund)

# Or, bulk register your functions
functions = {
    "your-cancel-function-id": cancel_order,
    "your-refund-function-id": refund,
}
client.register_functions(functions)

# Execute a chain
# Provide all initial variables needed to start the chain
result = client.run_chain({
    'message body': 'Hi, please cancel my order',
    'order id': '33433',
})

print("Chain completed:", result)
```

## Function Requirements

All registered functions **must** follow these requirements:

### Function Signature
Your functions should accept a single dictionary argument containing the inputs for that function call step:

```python
def my_function(args: dict) -> dict:
    # Your business logic here
    pass
```

**How it works:**
1. You define variables in your chain on chainix.ai (e.g., `order id`, `user email`, `action`)
2. You create function call steps in your chain and specify which variables should be passed as inputs to each step
3. When the chain reaches a function call step, it stops and calls your registered function via it's id
4. Your function receives a dictionary where each key is a variable you specified as an input for that step, and each value is the current value of that variable in the chain

**Example:** If you have a function call step with `order id` and `user email` as inputs, your function will receive:
```python
{
    'order id': '12345',
    'user email': 'user@example.com'
}
```

### Return Value
Your functions **must** return a dictionary with exactly two keys:

```python
{
    'success': bool,        # True if function executed successfully, False otherwise
    'vars_to_update': dict  # Dictionary of variables to update in the chain (can be empty)
}
```

**Important**: The keys in `vars_to_update` must exactly match the variable names you defined in your chain on chainix.ai. Only variables that exist in your chain can be updated. If you try to update a variable that doesn't exist in your chain, the chain will fail.

### Example Function Structure

```python
def process_order(args):
    try:
        # Extract arguments
        order_id = args['order id']
        action = args.get('action', 'process')
        
        # Your business logic here
        if action == 'cancel':
            # ... cancellation logic ...
            return {
                'success': True,
                'vars_to_update': {
                    'order status': 'cancelled',        # Must match variable name in your chain
                    'cancellation date': '2024-01-01'  # Must match variable name in your chain
                }
            }
        elif action == 'fulfill':
            # ... fulfillment logic ...
            return {
                'success': True,
                'vars_to_update': {
                    'order status': 'fulfilled',        # Must match variable name in your chain
                    'fulfillment date': '2024-01-01'   # Must match variable name in your chain
                }
            }
        else:
            return {
                'success': False,
                'vars_to_update': {}
            }
            
    except Exception as e:
        print(f"Error processing order: {e}")
        return {
            'success': False,
            'vars_to_update': {}
        }
```

## Function Registration

You can register functions individually or in bulk:

```python
# Individual registration
client.register_function("function-id-1", my_function)

# Bulk registration
functions = {
    "function-id-1": cancel_order,
    "function-id-2": refund,
    "function-id-3": process_order,
}
client.register_functions(functions)
```

## Configuration

```python
client = AsyncChainClient(
    chain_id="your-chain-id",           # Your unique chain identifier
    api_key="your-api-key",             # Your API key for authentication
    base_url="https://chainix.ai",      # Base URL (optional, defaults to chainix.ai)
    max_wait_time=300,                  # Max wait time in seconds (optional, default 300)
    poll_interval=5,                    # How often to check status in seconds (optional, default 5, minimum 3)
    verbose=True                        # Whether to print status messages (optional, default True)
)
```

### Silent Mode

For production environments or when you don't want status messages, you can disable verbose output:

```python
client = AsyncChainClient(
    chain_id="your-chain-id",
    api_key="your-api-key",
    verbose=False  # Runs silently
)
```

## Running Chains

### Basic Usage

```python
result = client.run_chain(
    initial_variables={
        'message body': 'Hi, please cancel my order',
        'user email': 'user@example.com',
        'order id': '12345',
    }
)
```

### Test Mode

You can run chains in test mode for development and debugging:

```python
result = client.run_chain(
    initial_variables={
        'message body': 'Hi, please cancel my order',
        'user email': 'user@example.com',
        'order id': '12345'
    },
    test=True  # Runs in test mode
)
```

## Error Handling

The client automatically handles several types of errors:

- **Network errors**: Automatically retries with backoff
- **Function execution errors**: Functions that throw exceptions are treated as failed (`success: False`)
- **Invalid function returns**: If functions don't return the required structure, the chain will stop with a clear error message

### Best Practices

1. **Always wrap the body of your custom function in try-catch blocks**, catch any errors and set success to false in the return dictionary
2. **Return meaningful error information** when functions fail
3. **Validate input arguments** at the start of your functions
4. **Use exact variable names** in `vars_to_update` that match your variables names on the chain configuration on chainix.ai

```python
def robust_function(args):
    try:
        # Validate inputs
        if 'required_field' not in args:
            raise ValueError("Missing required_field")
            
        # Your business logic
        result = perform_business_logic(args)
        
        return {
            'success': True,
            'vars_to_update': {
                'operation result': result,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return {
            'success': False,
            'vars_to_update': {'error type': 'validation_error'}
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'success': False,
            'vars_to_update': {'error type': 'unexpected_error'}
        }
```

## License

MIT License