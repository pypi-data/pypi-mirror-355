"""Calculate players features."""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements
import math
import multiprocessing
import statistics
from typing import Any
from warnings import simplefilter

import pandas as pd
import tqdm
from scipy.stats import kurtosis, sem, skew  # type: ignore

from .columns import DELIMITER
from .identifier import Identifier

PLAYERS_COLUMN = "players"


def _pool_process(
    row: tuple, team_identifiers: dict[str, list[Identifier]], df_cols: list[str]
) -> tuple[dict[str, float], Any]:
    row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}

    output = {}
    for column_prefix, player_identifiers in team_identifiers.items():
        columns: dict[str, list[float]] = {}

        for identifier in player_identifiers:
            for key, value in row_dict.items():
                if not key.startswith(identifier.column_prefix):
                    continue
                if not isinstance(value, float):
                    continue
                if math.isnan(value) or math.isinf(value):
                    continue
                column = key[len(identifier.column_prefix) :]
                columns[column] = columns.get(column, []) + [value]

        for column, values in columns.items():
            if not values or len(values) < 2:
                continue
            mean_column = DELIMITER.join(
                [column_prefix, PLAYERS_COLUMN, column, "mean"]
            )
            output[mean_column] = statistics.mean(values)

            median_column = DELIMITER.join(
                [column_prefix, PLAYERS_COLUMN, column, "median"]
            )
            output[median_column] = statistics.median(values)

            min_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "min"])
            output[min_column] = min(values)

            max_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "max"])
            output[max_column] = max(values)

            count_column = DELIMITER.join(
                [column_prefix, PLAYERS_COLUMN, column, "count"]
            )
            output[count_column] = float(len(values))

            sum_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "sum"])
            output[sum_column] = sum(values)

            var_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "var"])
            output[var_column] = statistics.variance(values)

            std_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "std"])
            output[std_column] = statistics.stdev(values)

            skew_column = DELIMITER.join(
                [column_prefix, PLAYERS_COLUMN, column, "skew"]
            )
            output[skew_column] = skew(values)

            kurt_column = DELIMITER.join(
                [column_prefix, PLAYERS_COLUMN, column, "kurt"]
            )
            output[kurt_column] = kurtosis(values)

            sem_column = DELIMITER.join([column_prefix, PLAYERS_COLUMN, column, "sem"])
            output[sem_column] = sem(values)

    return output, row[0]


def players_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Process players stats on a team."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df_dict: dict[str, list[float | None]] = {}
    df_cols = df.columns.values.tolist()

    team_identifiers: dict[str, list[Identifier]] = {}
    for identifier in identifiers:
        if identifier.team_identifier_column is None:
            continue
        team_identifier = [
            x for x in identifiers if x.column == identifier.team_identifier_column
        ]
        team_identifiers[team_identifier[0].column_prefix] = team_identifiers.get(
            team_identifier[0].column_prefix, []
        ) + [identifier]

    written_columns = set()
    with multiprocessing.Pool() as pool:
        for output, idx in pool.starmap(
            _pool_process,
            tqdm.tqdm(
                ((x, team_identifiers, df_cols) for x in df.itertuples(name=None)),
                desc="Players Processing",
                total=len(df),
            ),
        ):
            for k, v in output.items():
                if k not in df_dict:
                    df_dict[k] = [None for _ in range(len(df))]
                df_dict[k][idx] = v
                written_columns.add(k)

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    return df[sorted(df.columns.values.tolist())].copy()
