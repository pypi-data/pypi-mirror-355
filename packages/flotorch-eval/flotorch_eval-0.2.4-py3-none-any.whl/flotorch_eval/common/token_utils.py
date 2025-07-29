from typing import List
from flotorch_eval.agent_eval.core.schemas import (
    TokenUsageRecord,
    TokenUsageSummary,
    TokenTotals,
    Trajectory,
)

def extract_token_usage_from_trajectory(trajectory: Trajectory) -> TokenUsageSummary:
    records = []
    total_input = 0
    total_output = 0

    for span in trajectory.spans:
        attributes = span.attributes

        # CrewAI-style
        input_tokens = attributes.get("gen_ai.usage.input_tokens")
        output_tokens = attributes.get("gen_ai.usage.output_tokens")

        # Strands-style fallback
        if input_tokens is None and output_tokens is None:
            input_tokens = attributes.get("gen_ai.usage.prompt_tokens")
            output_tokens = attributes.get("gen_ai.usage.completion_tokens")

        model = attributes.get("gen_ai.response.model") or attributes.get("gen_ai.request.model")

        if input_tokens is not None and output_tokens is not None and model:
            record = TokenUsageRecord(
                span_name=span.name,
                span_id=span.span_id,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )
            records.append(record)
            total_input += input_tokens
            total_output += output_tokens

    return TokenUsageSummary(
        token_usage=records,
        totals=TokenTotals(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output
        )
    )
