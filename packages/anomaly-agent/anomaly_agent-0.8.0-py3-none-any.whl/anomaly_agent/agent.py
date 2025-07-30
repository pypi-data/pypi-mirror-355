"""
Anomaly detection agent using LLMs to identify and verify anomalies in time series data.

This module provides functionality for detecting and verifying anomalies in time series
data using language models.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional, TypedDict

import numpy as np
import pandas as pd
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field, validator

from .constants import DEFAULT_MODEL_NAME, DEFAULT_TIMESTAMP_COL, TIMESTAMP_FORMAT
from .prompt import get_detection_prompt, get_verification_prompt, DEFAULT_SYSTEM_PROMPT, DEFAULT_VERIFY_SYSTEM_PROMPT


class Anomaly(BaseModel):
    """Represents a single anomaly in a time series."""

    timestamp: str = Field(description="The timestamp of the anomaly")
    variable_value: float = Field(
        description="The value of the variable at the anomaly timestamp"
    )
    anomaly_description: str = Field(description="A description of the anomaly")

    @validator("timestamp")  # type: ignore
    def validate_timestamp(cls, v: str) -> str:
        """Validate that the timestamp is in a valid format."""
        try:
            # Try parsing with our custom format first
            datetime.strptime(v, TIMESTAMP_FORMAT)
            return v
        except ValueError:
            try:
                # Try parsing as ISO format
                dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                # If input had microseconds, preserve them
                if "." in v:
                    return dt.strftime(TIMESTAMP_FORMAT)
                # Otherwise use second precision
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # Try parsing as date only (add time component)
                    dt = datetime.strptime(v, "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # Try parsing without microseconds
                        dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                        return v  # Return original format
                    except ValueError:
                        raise ValueError(
                            f"timestamp must be in {TIMESTAMP_FORMAT} format, "
                            "ISO format, or YYYY-MM-DD format"
                        )

    @validator("variable_value")  # type: ignore
    def validate_variable_value(cls, v: float) -> float:
        """Validate that the variable value is a number."""
        if not isinstance(v, (int, float)):
            raise ValueError("variable_value must be a number")
        return float(v)

    @validator("anomaly_description")  # type: ignore
    def validate_anomaly_description(cls, v: str) -> str:
        """Validate that the anomaly description is a string."""
        if not isinstance(v, str):
            raise ValueError("anomaly_description must be a string")
        return v


class AnomalyList(BaseModel):
    """Represents a list of anomalies."""

    anomalies: List[Anomaly] = Field(description="The list of anomalies")

    @validator("anomalies")  # type: ignore
    def validate_anomalies(cls, v: List[Anomaly]) -> List[Anomaly]:
        """Validate that anomalies is a list."""
        if not isinstance(v, list):
            raise ValueError("anomalies must be a list")
        return v


class AgentState(TypedDict, total=False):
    """State for the anomaly detection agent."""

    time_series: str
    variable_name: str
    detected_anomalies: Optional[AnomalyList]
    verified_anomalies: Optional[AnomalyList]
    current_step: str


def create_detection_node(llm: ChatOpenAI, detection_prompt: str = DEFAULT_SYSTEM_PROMPT) -> ToolNode:
    """Create the detection node for the graph."""
    chain = get_detection_prompt(detection_prompt) | llm.with_structured_output(AnomalyList)

    def detection_node(state: AgentState) -> AgentState:
        """Process the state and detect anomalies."""
        result = chain.invoke(
            {
                "time_series": state["time_series"],
                "variable_name": state["variable_name"],
            }
        )
        return {"detected_anomalies": result, "current_step": "verify"}

    return detection_node


def create_verification_node(llm: ChatOpenAI, verification_prompt: str = DEFAULT_VERIFY_SYSTEM_PROMPT) -> ToolNode:
    """Create the verification node for the graph."""
    chain = get_verification_prompt(verification_prompt) | llm.with_structured_output(AnomalyList)

    def verification_node(state: AgentState) -> AgentState:
        """Process the state and verify anomalies."""
        if state["detected_anomalies"] is None:
            return {"verified_anomalies": None, "current_step": "end"}

        detected_str = "\n".join(
            [
                (
                    f"timestamp: {a.timestamp}, "
                    f"value: {a.variable_value}, "  # noqa: E501
                    f"Description: {a.anomaly_description}"  # noqa: E501
                )
                for a in state["detected_anomalies"].anomalies
            ]
        )

        result = chain.invoke(
            {
                "time_series": state["time_series"],
                "variable_name": state["variable_name"],
                "detected_anomalies": detected_str,  # noqa: E501
            }
        )
        return {"verified_anomalies": result, "current_step": "end"}

    return verification_node


def should_verify(state: AgentState) -> Literal["verify", "end"]:
    """Determine if we should proceed to verification."""
    return "verify" if state["current_step"] == "verify" else "end"


class AnomalyAgent:
    """Agent for detecting and verifying anomalies in time series data."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        timestamp_col: str = DEFAULT_TIMESTAMP_COL,
        verify_anomalies: bool = True,
        detection_prompt: str = DEFAULT_SYSTEM_PROMPT,
        verification_prompt: str = DEFAULT_VERIFY_SYSTEM_PROMPT,
    ):
        """Initialize the AnomalyAgent with a specific model.

        Args:
            model_name: The name of the OpenAI model to use
            timestamp_col: The name of the timestamp column
            verify_anomalies: Whether to verify detected anomalies (default: True)
            detection_prompt: System prompt for anomaly detection.
                Defaults to the standard detection prompt.
            verification_prompt: System prompt for anomaly verification.
                Defaults to the standard verification prompt.
        """
        self.llm = ChatOpenAI(model=model_name)
        self.timestamp_col = timestamp_col
        self.verify_anomalies = verify_anomalies
        self.detection_prompt = detection_prompt
        self.verification_prompt = verification_prompt

        # Create the graph
        self.graph = StateGraph(AgentState)

        # Add nodes
        self.graph.add_node("detect", create_detection_node(self.llm, detection_prompt))
        if self.verify_anomalies:
            self.graph.add_node("verify", create_verification_node(self.llm, verification_prompt))

        # Add edges with proper routing
        if self.verify_anomalies:
            self.graph.add_conditional_edges(
                "detect", should_verify, {"verify": "verify", "end": END}
            )
            self.graph.add_edge("verify", END)
        else:
            self.graph.add_edge("detect", END)

        # Set entry point
        self.graph.set_entry_point("detect")

        # Compile the graph
        self.app = self.graph.compile()

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        timestamp_col: Optional[str] = None,
        verify_anomalies: Optional[bool] = None,
    ) -> Dict[str, AnomalyList]:
        """Detect anomalies in the given time series data.

        Args:
            df: DataFrame containing the time series data
            timestamp_col: Name of the timestamp column (optional)
            verify_anomalies: Whether to verify detected anomalies. If None, uses the
                instance default (default: None)

        Returns:
            Dictionary mapping column names to their respective AnomalyList
        """
        if timestamp_col is not None:
            self.timestamp_col = timestamp_col

        # Use instance default if verify_anomalies not specified
        verify_anomalies = (
            self.verify_anomalies if verify_anomalies is None else verify_anomalies
        )

        # Create a new graph for this detection run
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("detect", create_detection_node(self.llm, self.detection_prompt))
        if verify_anomalies:
            graph.add_node("verify", create_verification_node(self.llm, self.verification_prompt))

        # Add edges with proper routing
        if verify_anomalies:
            graph.add_conditional_edges(
                "detect", should_verify, {"verify": "verify", "end": END}
            )
            graph.add_edge("verify", END)
        else:
            graph.add_edge("detect", END)

        # Set entry point
        graph.set_entry_point("detect")

        # Compile the graph
        app = graph.compile()

        # Check if timestamp column exists
        if self.timestamp_col not in df.columns:
            raise KeyError(
                f"Timestamp column '{self.timestamp_col}' not found in DataFrame"
            )

        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # If no numeric columns found, return empty results for all columns
        if len(numeric_cols) == 0:
            return {
                col: AnomalyList(anomalies=[])
                for col in df.columns
                if col != self.timestamp_col
            }

        # Convert DataFrame to string format
        df_str = df.to_string(index=False)

        # Process each numeric column
        results = {}
        for col in numeric_cols:
            # Create state for this column
            state = {
                "time_series": df_str,
                "variable_name": col,
                "current_step": "detect",
            }

            # Run the graph
            result = app.invoke(state)
            if verify_anomalies:
                results[col] = result["verified_anomalies"] or AnomalyList(anomalies=[])
            else:
                results[col] = result["detected_anomalies"] or AnomalyList(anomalies=[])

        return results

    def get_anomalies_df(
        self, anomalies: Dict[str, AnomalyList], format: str = "long"
    ) -> pd.DataFrame:
        """Convert anomalies to a DataFrame.

        Args:
            anomalies: Dictionary mapping column names to their respective
                AnomalyList
            format: Output format, either "long" or "wide"

        Returns:
            DataFrame containing the anomalies
        """
        if format not in ["long", "wide"]:
            raise ValueError("format must be either 'long' or 'wide'")

        if format == "long":
            # Create long format DataFrame
            rows = []
            for col, anomaly_list in anomalies.items():
                for anomaly in anomaly_list.anomalies:
                    rows.append(
                        {
                            "timestamp": pd.to_datetime(anomaly.timestamp),
                            "variable_name": col,
                            "value": anomaly.variable_value,
                            "anomaly_description": anomaly.anomaly_description,
                        }
                    )
            return pd.DataFrame(rows)

        # Create wide format DataFrame
        rows = []
        for col, anomaly_list in anomalies.items():
            for anomaly in anomaly_list.anomalies:
                rows.append(
                    {
                        "timestamp": pd.to_datetime(anomaly.timestamp),
                        col: anomaly.variable_value,
                        f"{col}_description": anomaly.anomaly_description,
                    }
                )
        return pd.DataFrame(rows)
