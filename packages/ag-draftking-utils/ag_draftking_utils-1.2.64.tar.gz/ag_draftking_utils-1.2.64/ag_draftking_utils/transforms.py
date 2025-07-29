from ag_draftking_utils.util import time_function
import pandas as pd
import numpy as np
import time
import os


def join_window_df_with_original_df(window_df, original_df, rename_cols, groupby_col):
    # this operation forces the index to return to its original value before the transform
    # so that it can be joined to the original dataframe correctly
    window_df = window_df.reset_index().set_index('level_1').drop(columns=[groupby_col])

    # the rolling stat columns are presently just named the actual stat, so rename them
    # to Trailing Window to reflect that they are trailing stats
    window_df = window_df.rename(columns=rename_cols)

    # rejoin with the original dataframe
    window_df = window_df.merge(original_df, left_index=True, right_index=True)

    assert window_df.shape[0] == original_df.shape[0]
    return window_df


def create_trailing_game_features(window_size, df, features, *rolling_window_function_args,
                                  groupby_col='player_id', min_period=1,
                                  rename_cols={}, rolling_window_function=np.mean,
                                  **rolling_window_function_kwargs):
    """
    Inputs:
        window_stats: List[str]: list of desired features to get window on (i.e. PTS_PAINT, SPD, SCREEN_AST_PTS, etc.)
        window_size: int: do you want trailing 5 games, trailing 10 games, etc...
        df: pd.DataFrame: inputs containing
            - GAME_DATE: date
            - NBA_PLAYER_ID: int
            - PLAYER_NAME: str
            - NBA_TEAM_ID: int
            - window_stats (must be numeric)
            - other_stats
    Outputs:
        pd.DataFrame: contains
            - GAME_DATE
            - NBA_PLAYER_ID
            - PLAYER_NAME
            - NBA_TEAM_ID
            - Trailing<window_size><window_stat>
        feature_names: List[str]
            gives you a list of the name of resulting features that you get from calling this function
    """

    # get the rolling average
    window_df = df.groupby(groupby_col)[features] \
                  .rolling(window=window_size, min_periods=min_period).aggregate(
        rolling_window_function, *rolling_window_function_args, **rolling_window_function_kwargs
    )

    # need to shift by 1 to exclude the current game
    window_df_ex_current = window_df.groupby([groupby_col]).shift(1)

    # check for each column that there's exactly 1 missing entry per player.
    # For some stats this will not be the case as they may not have existed
    # prior to a given year (i.e. if boxouts began getting recorded in 2017
    # then, 2015 boxout stats will show up as null)
    n_players = df[groupby_col].unique().shape[0]
    missing_data = window_df_ex_current[features].isna().sum()
    assert (missing_data == n_players).mean() > 0.5

    # ensure that a player's very first opportunity he has a value of -999...
    # This prevents peaking from occurring in the "not ex_current" columns.
    # if fillna to 0, then it creates a confound with trailing averages that are organically 0.
    window_df_ex_current[features] = window_df_ex_current.fillna(-999)

    final = join_window_df_with_original_df(window_df_ex_current, df, rename_cols, groupby_col)
    return final