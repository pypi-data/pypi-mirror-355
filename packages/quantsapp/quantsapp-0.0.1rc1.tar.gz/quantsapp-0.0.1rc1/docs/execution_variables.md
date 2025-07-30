# Variables to be used in Execution Module


## Usage

```python title="Steps to use Execution variables" hl_lines="8-16"
# Create the Execution object
import quantsapp
qapp_execution = quantsapp.Execution(
    session_context=session_context, # (1)!
)

# Now the variables can be used like below examples
qapp_execution.variables.Exchange.NSE_FNO # (2)!
qapp_execution.variables.Broker.DHAN # (3)!
qapp_execution.variables.BrokerRole.EXECUTOR # (4)!
qapp_execution.variables.BrokerAccountValidity.EXPIRED # (5)!
qapp_execution.variables.OrderBuySell.BUY # (6)!
qapp_execution.variables.OrderProductType.INTRADAY # (7)!
qapp_execution.variables.OrderType.LIMIT # (8)!
qapp_execution.variables.OrderStatus.COMPLETED # (9)!
qapp_execution.variables.OrderValidity.DAY # (10)!
```

1. Get the Before `session_context` via [Login](login.md) to Quantsapp
2. [`Exchange`](execution_variables.md#quantsapp._execution._enums.Exchange) variable
3. [`Broker`](execution_variables.md#quantsapp._execution._enums.Broker) variable
4. [`BrokerRole`](execution_variables.md#quantsapp._execution._enums.BrokerRole) variable
5. [`BrokerAccountValidity`](execution_variables.md#quantsapp._execution._enums.BrokerAccountValidity) variable
6. [`OrderBuySell`](execution_variables.md#quantsapp._execution._enums.OrderBuySell) variable
7. [`OrderProductType`](execution_variables.md#quantsapp._execution._enums.OrderProductType) variable
8. [`OrderType`](execution_variables.md#quantsapp._execution._enums.OrderType) variable
9. [`OrderStatus`](execution_variables.md#quantsapp._execution._enums.OrderStatus) variable
10. [`OrderValidity`](execution_variables.md#quantsapp._execution._enums.OrderValidity) variable

---

::: quantsapp._execution._enums.Exchange
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.Broker
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.BrokerAccountValidity
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.BrokerRole
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.OrderBuySell
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.OrderProductType
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.OrderType
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.OrderValidity
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true

---

::: quantsapp._execution._enums.OrderStatus
    options:
        show_root_heading: true
        show_root_full_path: false
        show_if_no_docstring: true
        show_labels: false
        show_symbol_type_toc: true
        show_category_heading: true