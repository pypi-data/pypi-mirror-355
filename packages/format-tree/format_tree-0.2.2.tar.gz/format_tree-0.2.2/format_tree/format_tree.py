import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from sklearn.tree import plot_tree, DecisionTreeClassifier
from typing import List, Optional, Tuple

def plot_formatted_tree(
    decision_tree, 
    feature_names=None,
    class_names=None,
    samples_format="number",    # "percentage" or "number"
    value_format="percentage",  # "percentage" or "number" (default).
    max_decimal_places=1,       # Maximum decimal places for formatting
    integer_thresholds=False,   # Whether to display thresholds as integers
    class_display="all",        # "all" or "one" - how to display class names
    figsize=(20, 10),
    display_missing=True,       # Whether to display missing values in the tree
    node_ids=True,              # Whether to display node IDs
    X_train=None,               # Feature data used to train the decision tree
    df=None,                    # DataFrame containing the data used to train the decision tree
    columns_to_check=None,      # List of columns to check for null values in each leaf node
    filled=True,                # Whether to fill the nodes with color
    rounded=True,               # Whether to round node values
    **kwargs  
):
    """
    Plot a decision tree with formatted node information.

    Parameters:
        decision_tree (sklearn.tree.DecisionTreeClassifier): The decision tree to plot.
        feature_names (list): List of feature names to use in the plot.
        class_names (list): List of class names to use in the plot.
        samples_format (str): Format for displaying samples in each node: "percentage" or "number" (default).
        value_format (str): Format for displaying values in each node: "percentage" or "number" (default).
        max_decimal_places (int): Maximum number of decimal places to display in node values (default: 1).
        integer_thresholds (bool): Whether to display thresholds as integers (default: False).
        class_display (str): How to display class names in the plot: "all" or "one" (default).
        figsize (tuple): The size of the figure in inches (default: (20, 10)).
        display_missing (bool): Whether to display missing values in the tree (default: True).
        node_ids (bool): Whether to display node IDs (must be True if display_missing is True).
        X_train (array or pd.DataFrame): Feature data used to train the decision tree (needed if display_missing is True).
        df (pd.DataFrame): DataFrame containing the data used to train the decision tree, if None, X_train is used (needed if display_missing is True).
        columns_to_check (list): List of columns to check for null values in each leaf node (needed if display_missing is True).
        filled (bool): Whether to fill the nodes with color (default: True).
        rounded (bool): Whether to round node values (default: True).
        **kwargs: Additional arguments to pass to `sklearn.tree.plot_tree()`.

    Returns:
        fig, ax: The matplotlib figure and axes objects.
    """
    # Validate input parameters
    if value_format not in ["percentage", "number"]:
        raise ValueError("value_format must be 'percentage' or 'number'")
    if samples_format not in ["percentage", "number"]:
        raise ValueError("samples_format must be 'percentage' or 'number'")
    if class_display not in ["all", "one"]:
        raise ValueError("class_display must be 'all' or 'one'")
        
    # Get total training sample size
    total_samples = float(decision_tree.tree_.weighted_n_node_samples[0])
    if total_samples <= 0:
        raise ValueError("Total samples must be greater than 0")
    
    # Validate display_missing and related parameters
    if display_missing:
        if not node_ids:
            raise ValueError("If display_missing is True, node_ids must also be True.")
        if X_train is None:
            raise ValueError("If display_missing is True, X_train (feature data) must be provided.")
        if columns_to_check is None or not isinstance(columns_to_check, (list, tuple)) or len(columns_to_check) == 0:
            raise ValueError("If display_missing is True, columns_to_check must be provided and non-empty.")

        # Find a list of node IDs with missing values
        nulls_in_leaf_nodes = get_nulls_in_leaf_nodes(decision_tree, X_train, columns_to_check, df)
        null_nodes = list(nulls_in_leaf_nodes.keys()) if nulls_in_leaf_nodes else []
    
    # Create the figure and plot the tree
    fig, ax = plt.subplots(figsize=figsize)
    plot_tree(
        decision_tree,
        feature_names=feature_names,
        class_names=class_names,
        filled=filled, 
        rounded=rounded,
        node_ids=node_ids,
        proportion=False,  # Always show absolute numbers
        **kwargs
    )
    
    # Find all the text boxes in the tree visualization
    for text in ax.texts:
        content = text.get_text()
        updated_content = content
        
        # Format samples field if present
        if 'samples = ' in content:
            samples_match = re.search(r'samples = (\d+)', content)
            if samples_match:
                node_samples = int(samples_match.group(1))
                
                # Format samples if needed
                if samples_format == "percentage":
                    samples_percent = (100.0 * node_samples / total_samples)
                    samples_str = str(round(samples_percent, max_decimal_places)) + "%"
                    updated_content = re.sub(
                        r'samples = \d+', 
                        f'samples = {samples_str}', 
                        updated_content
                    )
        
        # Format value field if present
        if 'value = [' in content:
            value_match = re.search(r'value = \[(.*?)\]', updated_content)
            if value_match:
                value_str = value_match.group(1)
                values = [float(v.strip()) for v in value_str.split(',')]

                # Convert values to percentage if needed
                if value_format == "percentage":
                    formatted_values = []
                    for v in values:
                        pct = (v / node_samples) * 100
                        if pct == int(pct):
                            formatted_values.append(f"{int(pct)}%")
                        else:
                            formatted_values.append(f"{pct:.{max_decimal_places}f}%")
                    formatted_values_str = ", ".join(formatted_values)
                    updated_content = re.sub(
                        r'value = \[.*?\]', 
                        f'value = [{formatted_values_str}]',
                        updated_content
                    )
        
        # Format class - handle class display options
        if class_display == "all" and class_names is not None and len(class_names) > 0:
            class_match = re.search(r'class = ([^\n]+)', updated_content)
            if class_match:
                class_str = class_names
                updated_content = re.sub(
                    r'class = ([^\n]+)', 
                    f'class = {class_str}',
                    updated_content
                )

        # Format sample - handle display_missing options
        if display_missing and node_ids:
            if null_nodes and 'samples =' in updated_content:
                # Check if the node id in updated_content matches any in null_nodes
                node_id_match = re.search(r'node #(\d+)', updated_content)
                if node_id_match:
                    node_id = int(node_id_match.group(1))
                    if node_id in null_nodes:
                        updated_content = updated_content.replace('samples =', 'samples (with null) =')
                
        # Format threshold to integer if requested
        if integer_thresholds and ('<=' in content):
            threshold_match = re.search(r'([<=>]+) (\d+\.\d+)', content)
            if threshold_match:
                comparison = threshold_match.group(1)
                threshold = float(threshold_match.group(2))
                
                # Adjust threshold formatting based on comparison
                if comparison == "<=":
                    new_threshold = int(threshold)
                    updated_content = updated_content.replace(
                        f"{comparison} {threshold}", 
                        f"<= {new_threshold}"
                    )
                   
        # Update the text if it changed
        if updated_content != content:
            text.set_text(updated_content)
    
    plt.tight_layout()
    return fig, ax


def check_nulls_in_leaf_nodes(df, leaf_node_column, columns_to_check):
    """
    Checks for null values in specific columns for each leaf node and returns a dictionary for the leaf nodes with null values.

    Parameters:
        df (pd.DataFrame): The dataframe containing the data.
        leaf_node_column (str): The column name representing the leaf nodes.
        columns_to_check (list): List of column names to check for null values.

    Returns:
        dict: A dictionary containing information about null values in each leaf node.
            {
                'null_count': int,                 # Number of samples with at least one null in the specified columns within this leaf node.
                'sample_indices': list of int,     # List of DataFrame indices for samples with nulls in the specified columns.
                'total_samples_in_leaf': int       # Total number of samples in this leaf node.
            }
            Only leaf nodes containing at least one null value in the specified columns are included in the output dictionary.
    """

    # Initialize an empty dictionary to store the results
    null_by_leaf = {}

    # Loop over each unique leaf node
    for leaf_node in np.unique(df[leaf_node_column]):
        # Select the samples for the current leaf node
        leaf_samples = df[df[leaf_node_column] == leaf_node]

        # Loop over each column to check for null values
        for column in columns_to_check:
            # Check if the column is in the DataFrame
            if column not in leaf_samples.columns:
                raise ValueError(f"Column '{column}' not found in DataFrame.")

            # Count the number of null values in the current column
            null_count = leaf_samples[column].isnull().sum()

            # If there are null values, add the information to the dictionary
            if null_count > 0:
                # Initialize an empty dictionary for the current column
                null_by_column = {}

                # Store the null counts and sample indices in the dictionary
                null_by_column[column] = {
                    'null_count': null_count,  # Number of samples with null in this column
                    'sample_indices': leaf_samples[leaf_samples[column].isnull()].index.tolist(),  # Indices of samples with nulls in this column
                    'total_samples_in_leaf': len(leaf_samples)  # Total number of samples in this leaf node
                }

                # Add the null counts for this column to the leaf node
                if leaf_node not in null_by_leaf:
                    null_by_leaf[int(leaf_node)] = {}
                null_by_leaf[int(leaf_node)].update(null_by_column)

    # Return the dictionary
    return null_by_leaf


def get_nulls_in_leaf_nodes(decision_tree, X_train, columns_to_check, df=None):
    """
    Analyzes the distribution of null values within specified columns for each leaf node of a trained Decision Tree Model.

    This function assigns each sample to its corresponding leaf node, appends this information to the provided DataFrame, 
    and then inspects the specified columns for null values within each leaf node. It returns a mapping that details, 
    for every leaf node, the number of samples containing at least one null in the specified columns, the indices of these samples, 
    and the total number of samples assigned to that leaf node.

    Parameters:
        decision_tree (DecisionTreeClassifier or DecisionTreeRegressor): Trained Decision Tree Model.
        X_train (pd.DataFrame or np.ndarray): DataFrame or array containing features used for training the decision_tree.
        df (pd.DataFrame, optional): DataFrame to which the leaf node column will be added. If None, X_train is used.
        columns_to_check (list): List of columns to check for null values in each leaf node.

    Returns:
        dict: A mapping from each leaf node to a dictionary containing:
            - 'null_counts': int, number of samples in the leaf node with at least one null in the specified columns.
            - 'sample_indices': list of int, indices of samples with nulls in the specified columns.
            - 'total_samples_in_leaf': int, total number of samples assigned to the leaf node.
    """
    # Use X_train as df if df is None
    if df is None:
        if isinstance(X_train, np.ndarray):
            # Convert ndarray to DataFrame
            df = pd.DataFrame(X_train, columns=[f"feature_{i}" for i in range(X_train.shape[1])])
        else:
            # X_train is already a DataFrame
            df = X_train

    # Get leaf node assignments
    leaf_nodes = decision_tree.apply(X_train)

    # Add leaf node information to the DataFrame
    df_copy = df.copy()
    leaf_column = 'leaf_node'  # Name for the new leaf node column in the DataFrame
    df_copy[leaf_column] = leaf_nodes

    # Check for null values in each leaf node
    nulls_in_leaf_nodes = check_nulls_in_leaf_nodes(df_copy, leaf_column, columns_to_check)
    
    return nulls_in_leaf_nodes


def summarize_tree(
    decision_tree: DecisionTreeClassifier,
    feature_names: Optional[List[str]] = None,
    class_list: Optional[List[str]] = None,
    integer_thresholds: bool = False,
    display_missing: bool = True,
    X_train: Optional[pd.DataFrame] = None,
    df: Optional[pd.DataFrame] = None,
    columns_to_check: Optional[List[str]] = None,
    precision: int = 3,
) -> pd.DataFrame:
    """
    Summarizes a decision tree by traversing its nodes and collecting data about each leaf.

    Parameters:
        decision_tree: DecisionTreeClassifier.
        feature_names (list of str, optional): List of feature names.
        class_list (list of str, optional): List of class names.
        integer_thresholds (bool, optional): Flag to format thresholds as integers.
        display_missing (bool, optional): Flag to display missing values information.
        X_train: Feature data used to train the decision tree.
        df: DataFrame containing the data used to train the decision tree, if None, X_train is used.
        columns_to_check: List of columns to check for null values in each leaf node.
        precision: Number of decimal places to round values.

    Returns:
        pd.DataFrame: DataFrame containing leaf node conditions, sample sizes, and class distributions.
    """
    if decision_tree is None:
        raise ValueError("decision_tree must be a trained decision tree model.")

    # Extract tree properties
    tree = decision_tree.tree_
    children_left = tree.children_left
    children_right = tree.children_right
    feature_ids = tree.feature
    thresholds = tree.threshold
    n_classes = tree.value.shape[2]

    # Handle missing values if display_missing is True
    if display_missing:
        if X_train is None:
            raise ValueError("If display_missing is True, X_train (feature data) must be provided.")
        if columns_to_check is None or not isinstance(columns_to_check, (list, tuple)) or len(columns_to_check) == 0:
            raise ValueError("If display_missing is True, columns_to_check must be provided and non-empty.")
        nulls_in_leaf_nodes = get_nulls_in_leaf_nodes(decision_tree, X_train, columns_to_check, df)
        null_nodes = list(nulls_in_leaf_nodes.keys())
    else:
        nulls_in_leaf_nodes = {}
        null_nodes = []

    # Set default class list if not provided
    if class_list is None:
        class_list = [f'Class {i}' for i in range(n_classes)]

    def format_threshold(thresh: float) -> str:
        """Formats a float as a string with at most 4 decimal places, trimming trailing 0s and the decimal point if applicable."""
        s = f"{thresh:.4f}"
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s

    feature_order = []  # Keeps track of the order of features as they appear
    leaf_data = []  # Stores data about each leaf node

    def traverse(node_id: int, path_conditions: List[Tuple[int, float, str]]) -> None:
        """
        Recursively traverses the tree to collect leaf node data.

        Parameters:
            node_id (int): Current node ID in the tree.
            path_conditions (list): Conditions leading to the current node.
        """
        if children_left[node_id] == children_right[node_id]:  # Leaf node
            total_samples = tree.weighted_n_node_samples[node_id]
            if tree.n_outputs == 1:  # Check if the decision tree has only one output
                value = tree.value[node_id][0, :]
            else:
                value = tree.value[node_id]

            # Determine class distribution or regression value
            if tree.n_classes[0] != 1:  # Check if the tree is a classification tree
                value_pct = value
                value = value * tree.weighted_n_node_samples[node_id]

            if tree.n_classes[0] == 1:
                class_counts = np.around(value, precision)
            elif np.all(np.equal(np.mod(value, 1), 0)):
                class_counts = value.astype(int)
            else:
                class_counts = np.around(value, precision)

            if tree.n_classes[0] != 1:
                leaf_data.append((node_id, path_conditions, int(total_samples), class_counts, value_pct))
            else:
                leaf_data.append((node_id, path_conditions, int(total_samples), class_counts, None))
            return

        feat_id = feature_ids[node_id]
        thresh = thresholds[node_id]
        feat_name = feature_names[feat_id] if feature_names else feat_id

        if feat_name not in feature_order:
            feature_order.append(feat_name)

        # Recurse for left and right children
        traverse(children_left[node_id], path_conditions + [(feat_id, thresh, '<=')])
        traverse(children_right[node_id], path_conditions + [(feat_id, thresh, '>')])

    traverse(0, [])  # Start traversal from the root node

    rows = []  # List to store row data for DataFrame
    for leaf_id, conditions, sample_size, class_counts, value_pct in leaf_data:
        row = {'leaf_index': leaf_id}
        feat_bounds = {}  # Stores the bounds for features
        missing_feats = set()  # Track which features have missing values

        # Handle missing value tracking
        if display_missing:
            row['Missing Value'] = 'Y' if leaf_id in null_nodes else 'N'
            if leaf_id in nulls_in_leaf_nodes:
                missing_feats = set(nulls_in_leaf_nodes[leaf_id].keys())

        # Determine feature bounds
        for feat_id, thresh, ineq in conditions:
            feat_key = feature_names[feat_id] if feature_names else feat_id
            if feat_key not in feat_bounds:
                feat_bounds[feat_key] = {'lower': None, 'upper': None}

            if ineq == '>':
                if feat_bounds[feat_key]['lower'] is None or thresh > feat_bounds[feat_key]['lower']:
                    feat_bounds[feat_key]['lower'] = thresh
            else:  # '<='
                if feat_bounds[feat_key]['upper'] is None or thresh < feat_bounds[feat_key]['upper']:
                    feat_bounds[feat_key]['upper'] = thresh

        # Format feature bounds and handle missing data
        for feat in feature_order:
            if feat in feat_bounds:
                b = feat_bounds[feat]
                parts = []
                if b['lower'] is not None:
                    threshold = int(b['lower']) if integer_thresholds else format_threshold(b['lower'])
                    parts.append(f"> {threshold}") 
                if b['upper'] is not None:
                    threshold = int(b['upper']) if integer_thresholds else format_threshold(b['upper'])
                    parts.append(f"<= {threshold}")
                if feat in missing_feats:
                    parts.append("Missing")
                row[feat] = ', '.join(parts)
            else:
                row[feat] = "Missing" if feat in missing_feats else ''

        # Populate row with sample size and class information
        row['Sample Size'] = sample_size
        for i, cls in enumerate(class_list):
            row[cls] = int(class_counts[i])
            row[f"{cls}%"] = value_pct[i] if value_pct is not None else None

        rows.append(row)

    # Define column order for DataFrame
    if display_missing:
        col_order = ['leaf_index'] + feature_order + ['Missing Value', 'Sample Size'] + class_list + [f"{cls}%" for cls in class_list]
    else:
        col_order = ['leaf_index'] + feature_order + ['Sample Size'] + class_list + [f"{cls}%" for cls in class_list]

    return pd.DataFrame(rows)[col_order]


def convert_text_to_number_column(
    df: pd.DataFrame, 
    column_name: str, 
    min_value: int = 1, 
    max_value: int = 20
) -> pd.DataFrame:
    """
    Converts text descriptions of numerical ranges in a DataFrame column to standardized range text.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the column to be processed.
        column_name (str): The name of the column in the DataFrame that contains text descriptions of numerical ranges.
        min_value (int, optional): The minimum possible value for the range. Defaults to 1.
        max_value (int, optional): The maximum possible value for the range. Defaults to 20.

    Returns:
        pd.DataFrame: The original DataFrame with an additional column named '{column_name}_range', containing the 
                      standardized range text for each entry in the specified column.
    """

    def extract_bounds(text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extracts the lower and upper bounds from a text description of a numerical range.

        Parameters:
            text (str): The text description of the numerical range.

        Returns:
            tuple: A tuple containing the lower bound and upper bound of the range, or (None, None) if the text does not describe a range.
        """

        text = str(text)
        # Remove ", Missing" if present
        cleaned = text.split(", Missing")[0].strip()

        # Case: "<= number"
        match_le = re.match(r"<=\s*(\d+)", cleaned)
        if match_le:
            lower = min_value
            upper = int(match_le.group(1))
            return lower, upper

        # Case: "> number1, <= number2"
        match_between = re.match(r">\s*(\d+).*<=\s*(\d+)", cleaned)
        if match_between:
            lower = int(match_between.group(1)) + 1
            upper = int(match_between.group(2))
            return lower, upper

        # Case: "> number"
        match_gt = re.match(r">\s*(\d+)", cleaned)
        if match_gt:
            lower = int(match_gt.group(1)) + 1
            upper = max_value
            return lower, upper

        return None, None

    def make_range_text(row: pd.Series) -> str:
        """
        Transforms a numerical range description into a human-readable text representation.

        Parameters:
            row (pd.Series): A row of a DataFrame containing the range description.

        Returns:
            str: A human-readable text representation of the range. If the row contains a missing value, the returned string will include ", Missing".
        """
        lower, upper = extract_bounds(row[column_name])
        range_text = ""

        if lower is not None and upper is not None:
            if upper - lower == 1:
                range_text = f"{lower}, {upper}"
            else:
                range_text = f"{lower} - {upper}"
        elif lower is not None:
            range_text = f"{lower}"
        else:
            range_text = ""

        if row.get('Missing Value', '') == 'Y':
            if len(range_text) > 0:
                range_text += ", Missing"
            else:
                range_text = "Missing"

        return range_text

    df[f'{column_name}_range'] = df.apply(make_range_text, axis=1)
    return df
