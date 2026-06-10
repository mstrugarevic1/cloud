# [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Date
[YYYY-MM-DD]

## Owner
[Name]

## Context
[Describe the situation that led to the decision. Include what problem exists, why the decision is needed now, what limitations or pain points exist, and what happens if no decision is made.]

## Goals
[List what the decision should achieve.]

## Non-Goals
[List what is intentionally out of scope.]

## Constraints
[Mention relevant constraints such as existing systems, cost, security, compliance, team capacity, operational complexity, timeline, or backwards compatibility.]

## Options Considered

### [Option 1]
* **Description**: [Short description]
* **Advantages**: [Pros]
* **Disadvantages**: [Cons]
* **Risks**: [Known risks]

### [Option 2]
* **Description**: [Short description]
* **Advantages**: [Pros]
* **Disadvantages**: [Cons]
* **Risks**: [Known risks]

## Decision
[Clearly state the selected option.]

## Reasoning
[Explain why this option was selected. Include main tradeoffs, why other options were rejected, what complexity is being accepted, and why the decision makes sense in the current context.]

## Consequences

Positive consequences:
- [Benefit]

Negative consequences:
- [Drawback]

New complexity:
- [Complexity]

## Operational Impact
[Describe how the decision affects day-to-day operations. Include relevant details for deployment, monitoring, alerting, logging, incident response, runbooks, and on-call impact.]

## Security and Compliance Impact
[Describe any security or compliance impact. If none, write: No direct security or compliance impact identified.]

## Cost Impact
[Describe expected cost impact.]

## Rollout Plan
[Briefly describe how the decision will be introduced safely.]

## Rollback Plan
[Briefly describe how to recover if the decision causes problems.]

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| [Risk description] | [Impact description] | [Mitigation description] |

## Success Criteria
[Describe how the team will know the decision worked.]

## Related Documents
* [Document Title](link)

## Superseded By
[Link to newer ADR, if any]

---

## Example

# Use SQS with DLQ for asynchronous partner synchronization

## Status
Accepted

## Date
2023-10-15

## Owner
Alex Doe

## Context
Our core API synchronously forwards requests to a partner service. The partner service has degraded reliability and occasionally times out. These timeouts block API requests, leading to failed operations and resource starvation in our service. If no decision is made, errors will continue to spike during partner downtime.

## Goals
- Isolate our core API from partner service outages
- Ensure requests succeed even if the partner service is temporarily unavailable
- Retain all requests for eventual processing

## Non-Goals
- Real-time synchronization with the partner service

## Constraints
- Must not lose any synchronization events
- Cost must remain under existing cloud budget
- Must handle temporary partner outages of up to 4 hours

## Options Considered

### Synchronous retries with exponential backoff
* **Description**: Implement retries directly within the API handler.
* **Advantages**: Simple to implement, no new infrastructure required.
* **Disadvantages**: API still blocks during retries, does not solve resource starvation during extended outages.
* **Risks**: Connection pool exhaustion during prolonged downtime.

### Use SQS with Dead Letter Queue (DLQ)
* **Description**: Push requests to an SQS queue and process them with a separate background worker.
* **Advantages**: Fully decouples the core API from the partner service, high availability, handles long outages natively.
* **Disadvantages**: Adds infrastructure complexity, requires a new background worker service.
* **Risks**: Messages could be processed out of order.

### EventBridge
* **Description**: Use EventBridge to route events to a target handler.
* **Advantages**: Serverless routing, easy to extend with multiple targets.
* **Disadvantages**: Higher latency, more complex DLQ management compared to standard SQS.
* **Risks**: Potential payload size limits.

## Decision
Use SQS with a Dead Letter Queue (DLQ).

## Reasoning
SQS provides the simplest and most robust way to decouple our API from the partner service. It guarantees delivery and handles extended outages natively. We reject synchronous retries because they do not protect against prolonged downtime, and EventBridge introduces unnecessary routing complexity for a single point-to-point integration. The added operational complexity of maintaining a worker service is accepted to achieve the required reliability.

## Consequences

Positive consequences:
- Core API latency is no longer affected by partner service performance
- Partner outages do not cause failures

Negative consequences:
- Synchronization is strictly asynchronous

New complexity:
- A new background worker service must be deployed and maintained
- SQS queues and DLQs must be monitored

## Operational Impact
- Deployment: New worker service added to deployment pipeline.
- Monitoring: Need metrics for SQS queue depth and worker processing latency.
- Alerting: Alert if the DLQ receives messages or if queue depth exceeds 10,000 for more than 5 minutes.
- Runbooks: Create a runbook for inspecting and redriving DLQ messages.

## Security and Compliance Impact
No direct security or compliance impact identified.

## Cost Impact
Minor increase due to SQS request pricing and small compute resources for the worker service.

## Rollout Plan
1. Provision SQS and DLQ infrastructure.
2. Deploy the worker service to consume from SQS and call the partner service.
3. Update the core API to write to SQS instead of calling the partner synchronously, behind a feature flag.
4. Gradually enable the feature flag for a subset of traffic.

## Rollback Plan
1. Disable the feature flag to revert the core API to synchronous calls.
2. Allow the worker to drain any remaining messages in SQS.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Messages are processed more than once | Duplicate actions | Use idempotency keys |
| External API is unavailable | Processing delay | Retry with backoff and DLQ |

## Success Criteria
- Zero errors caused by partner service timeouts
- Partner outages are invisible to the core API
- DLQ alerts fire correctly during extended partner downtime

## Related Documents
- [Partner API Documentation](#)
- [Worker Service Runbook](#)

## Superseded By
N/A
