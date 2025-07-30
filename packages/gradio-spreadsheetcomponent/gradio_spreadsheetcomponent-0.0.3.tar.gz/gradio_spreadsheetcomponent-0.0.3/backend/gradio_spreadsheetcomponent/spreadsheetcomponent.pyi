from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

import numpy as np
import os
import pandas as pd
import tempfile
from gradio.utils import FileData
from gradio.components.base import Component, FormComponent
from gradio.events import Events
from gradio.i18n import I18nData
from huggingface_hub import InferenceClient

if TYPE_CHECKING:
    from gradio.components import Timer

from gradio.events import Dependency

class SpreadsheetComponent(FormComponent):
    """
    Creates a spreadsheet component that can display and edit tabular data with question answering capabilities.
    """
    
    def __init__(
        self,
        value: pd.DataFrame | list | dict | None = None,
        **kwargs
    ):
        """
        Parameters:
            value: Default value to show in spreadsheet. Can be a pandas DataFrame, list of lists, or dictionary
            hf_token: Hugging Face API token for question answering functionality
        """
        # Initialize the default value first
        if isinstance(value, list):
            value = pd.DataFrame(value)
        elif isinstance(value, dict):
            value = pd.DataFrame.from_dict(value)
        elif not isinstance(value, pd.DataFrame):
            raise ValueError(f"Value must be DataFrame, list, dict or None. Got {type(value)}")

        
        super().__init__(
            value=value,
            **kwargs,
        )

        self.value = value
            
        # Initialize Hugging Face client if token provided

        self.hf_client = InferenceClient(provider="hf-inference", api_key=os.getenv("HF_TOKEN"))
        
    def postprocess_answer(self, result) -> str:
        """Process and verify the model's answer, especially for aggregation operations."""
        try:
            # Extract answer and check if it's a number (potential aggregation)
            answer = getattr(result, 'answer', None)
            if not answer or str(answer).lower() in ['none', 'null', 'nan', '']:
                return "No answer found"

            # Detect aggregation keywords in the answer
            agg_keywords = {
                'sum': 'sum',
                'average': 'mean',
                'mean': 'mean',
                'maximum': 'max',
                'max': 'max',
                'minimum': 'min',
                'min': 'min',
                'count': 'count'
            }

            # Check if we need to verify any aggregation            
            operation = None
            for fun_name in agg_keywords.keys():
                if fun_name in str(result.aggregator.lower()):
                    operation = fun_name
                    break

            coordinates = getattr(result, 'coordinates', None)
            if operation and coordinates and len(coordinates) > 0:
                col_name = None
                try:
                    # Group coordinates by column to ensure we're working with consistent data
                    col_groups = {}
                    for row_idx, col_idx in coordinates:
                        if col_name is None:
                            col_name = self.value.columns[col_idx]
                        elif col_name != self.value.columns[col_idx]:
                            continue  # Skip if value is from a different column
                            
                        value = self.value.iloc[row_idx, col_idx]
                        if pd.notna(value):  # Only include non-NA values
                            col_groups.setdefault(col_name, []).append(value)
                    
                    if col_name and col_groups:
                        # Convert collected values to numeric, handling non-numeric values
                        numeric_values = pd.to_numeric(col_groups[col_name], errors='coerce')
                        
                        if len(numeric_values) > 0:
                            # Perform the aggregation on the specific values
                            if operation == 'sum':
                                computed_value = numeric_values.sum()
                            elif operation in ['mean', 'average']:
                                computed_value = numeric_values.mean()
                            elif operation in ['max', 'maximum']:
                                computed_value = numeric_values.max()
                            elif operation in ['min', 'minimum']:
                                computed_value = numeric_values.min()
                            elif operation == 'count':
                                computed_value = len(numeric_values)
                            else:
                                computed_value = None

                            # Format the computed value
                            if pd.notna(computed_value):
                                # Round floating point numbers to 2 decimal places
                                if isinstance(computed_value, float):
                                    computed_value = round(computed_value, 2)
                                
                                # Add verification to the answer
                                parts = []
                                parts.append(f"Answer: {computed_value}")
                                
                                # Add information about the cells used
                                cells = getattr(result, 'cells', None)
                                if cells:
                                    parts.append(f"Values used: {', '.join(str(x) for x in cells)}")
                                
                                parts.append(f"Column used: '{col_name}'")
                                parts.append(f"Number of values considered: {len(numeric_values)}")
                                
                                return "\n".join(parts)

                except Exception as calc_error:
                    # If calculation fails, return original answer with error info
                    parts = []
                    parts.append(f"Answer: {answer}")
                    parts.append(f"Note: Could not verify {operation} calculation: {str(calc_error)}")
                    return "\n".join(parts)

            # If no aggregation needed or verification failed, return the original formatted answer
            parts = []
            parts.append(f"Answer: {answer}")
            
            cells = getattr(result, 'cells', None)
            if cells:
                parts.append(f"Relevant cell values: {', '.join(str(x) for x in cells)}")
            
            coordinates = getattr(result, 'coordinates', None)    
            if coordinates:
                parts.append("Location of relevant information:")
                for coords in coordinates:
                    row_idx, col_idx = coords
                    col_name = self.value.columns[col_idx]
                    parts.append(f"- Row {row_idx}, Column '{col_name}'")
                    
            return "\n".join(parts)

        except Exception as e:
            return f"Error processing answer: {str(e)}"

    def answer_question(self, question: str) -> str:
        """Ask a question about the current spreadsheet data"""
        if self.hf_client is None:
            return "Error: Hugging Face API token not configured. Please provide a token through the hf_token parameter or HUGGINGFACE_API_TOKEN environment variable."
            
        try:
            if self.value.empty:
                return "Error: The spreadsheet is empty. Please add some data first."
                
            # Convert DataFrame to table format
            table = {col: [str(val) if pd.notna(val) else "" for val in self.value[col]] 
                    for col in self.value.columns}
            
            # Get answer using table question answering
            result = self.hf_client.table_question_answering(
                table=table,
                query=question,
                model="google/tapas-large-finetuned-wtq"
            )
            
            # Use postprocess_answer to handle the result
            return self.postprocess_answer(result)
            
        except Exception as e:
            return f"Error processing question: {str(e)}\nPlease try rephrasing your question or verify the data format."
    
    def api_info(self) -> dict[str, Any]:
        """Define component's API information for documentation."""
        return {
            "name": "spreadsheet",
            "description": "A spreadsheet component for data manipulation with question answering capabilities",
            "inputs": [
                {
                    "name": "value",
                    "type": "DataFrame | list | dict | None",
                    "description": "Data to display in the spreadsheet",
                    "default": None,
                    "required": False
                },
                {
                    "name": "headers",
                    "type": "List[str]",
                    "description": "Column headers for the spreadsheet",
                    "default": None,
                    "required": False
                },
                {
                    "name": "row_count",
                    "type": "int",
                    "description": "Default number of rows if no value provided",
                    "default": 3,
                    "required": False
                },
                {
                    "name": "col_count",
                    "type": "int",
                    "description": "Default number of columns if no value provided",
                    "default": 3,
                    "required": False
                }
            ],
            "outputs": [
                {
                    "name": "value",
                    "type": "DataFrame",
                    "description": "The current state of the spreadsheet"
                }
            ],
            "dependencies": [
                {"name": "pandas", "type": "pip"},
                {"name": "openpyxl", "type": "pip"},
                {"name": "huggingface-hub", "type": "pip"}
            ]
        }
    from typing import Callable, Literal, Sequence, Any, TYPE_CHECKING
    from gradio.blocks import Block
    if TYPE_CHECKING:
        from gradio.components import Timer
        from gradio.components.base import Component