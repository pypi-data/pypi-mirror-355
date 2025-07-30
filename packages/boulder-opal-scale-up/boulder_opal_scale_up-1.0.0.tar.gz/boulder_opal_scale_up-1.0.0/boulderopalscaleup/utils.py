from typing import Any


def display(headers: list[str], data: list[list]) -> None:
    """
    Example:
    headers = ["Name", "Age", "Occupation"]
    data = [
        ["Alice", 24, "Engineer"],
        ["Bob", 30, "Designer"],
        ["Charlie", 28, "Doctor"]
    ]
    _display(headers, data) will be displayed as:

    Name    | Age | Occupation
    ---------------------------
    Alice   | 24  | Engineer
    Bob     | 30  | Designer
    Charlie | 28  | Doctor
    """

    # Calculate column widths
    col_widths = [max(len(str(row[i])) for row in [headers, *data]) for i in range(len(headers))]

    # Format rows
    def format_row(row):
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    # Print table
    print(format_row(headers))  # noqa: T201
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))  # noqa: T201
    for row in data:
        print(format_row(row))  # noqa: T201
    print()  # noqa: T201


def transform(dataframelike: dict[str, dict[str, Any]]) -> tuple:
    """
    Given a dictionary like:
    {
        "frequency_high": {
            'value': 7.259297892461884,
            'std': None,
            'calibration status': 'unmeasured'
        },
        "frequency_low": {
            'value': 7.259297892461884,
            'std': None,
            'calibration status': 'unmeasured'
        }
    }
    returns:
    headers = ["frequency_high", "frequency_low"]
    data = [
        ["value", 7.259297892461884, 7.259297892461884],
        ["std", None, None],
        ["calibration status", 'unmeasured', 'unmeasured']
    ]
    """
    headers = dataframelike.keys()
    values_lst = ["value"]
    std_lst = ["std"]
    calibration_status_lst = ["calibration status"]

    for header in headers:
        values_lst.append(dataframelike[header]["value"])
        std_lst.append(dataframelike[header]["std"])
        calibration_status_lst.append(dataframelike[header]["calibration status"])
    data = [values_lst, std_lst, calibration_status_lst]
    return headers, data


def abstract_dict(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    display_data = {}

    for parameter, value in data.items():
        v = value
        tmp = {}
        scale = v.get("display", {}).get("scale", 1)
        unit: str = v.get("display", {}).get("unit", "")

        # Get value
        tmp["value"] = v.get("value") * scale

        # Get std
        tmp["std"] = (
            (v["err_plus"] + v["err_minus"]) * scale
            if v.get("err_plus", None) and v.get("err_minus", None)
            else None
        )

        # Get calibration status
        tmp["calibration status"] = v.get("calibration_status", "unknown")

        label = f"{parameter} ({unit})"
        display_data[label.strip()] = tmp

    return display_data


def display_node_information(n_name: str, n_value: dict[str, Any]) -> None:
    summary_data = abstract_dict(n_value)
    headers, data = transform(summary_data)

    display([f"node name: {n_name}", *list(headers)], data)
