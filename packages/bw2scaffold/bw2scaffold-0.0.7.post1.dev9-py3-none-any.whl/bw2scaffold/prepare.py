from code2flow.engine import SubsetParams, code2flow


def create_callgraph(
    file_path_input: str, file_path_output: str, function: str = "main"
):
    """Creates a callgraph of the workflow"""

    subset_params = SubsetParams(function, 5, 5)

    code2flow(
        file_path_input,
        file_path_output,
        subset_params=subset_params,
        hide_legend=False,
    )
