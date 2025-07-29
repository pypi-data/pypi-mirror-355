from ag_draftking_utils.util import time_function
import pandas as pd
import numpy as np
import time
import os


def remove_peeking(df, aggregate_columns, features_to_fix, ranking_column, peeking_column='date'):
    """
    When using play-by-play and trivially calculating the trailing N features, you run into situations
    where you're using trailing stats calculated from the same game (which you wouldn't know at inference)
    time. The idea here is to make the data such that you are only using the last piece of information 
    that you actually know at inference time.

    NOTE: must be pre-sorted ascending... 

    Inputs:
        df: pd.DataFrame - the data that you need to fix
        aggregate_columns: List[str] - the grouping that you are using. 
        features_to_fix: List[str] - the features which may have some peeking.
        ranking_column: str - this is how you determine the "first" observation.
        peeking_column: str - the granularity level that defines peeking.
    Outputs:
        pd.DataFrame -- the fixed dataframe
    """

    df['zzztmpRank'] = df.groupby(aggregate_columns+[peeking_column])[ranking_column].rank(method='min')

    nulls = np.full((df.shape[0], len(features_to_fix)), np.nan)
    # the idea here is to not use the trailing N at-bats for the 2nd, 3rd, ... Nth PA
    # because we don't yet know these values at the start of the game.
    df[features_to_fix] = np.where(
        (df['zzztmpRank'].to_numpy() == 1)[:, None],
        df[features_to_fix],
        nulls
    )
    # replace the now-null values with the 
    df[features_to_fix] = df.groupby(aggregate_columns)[features_to_fix].ffill()
    return df.drop(columns='zzztmpRank')


def _join_window_df_with_original_df(window_df, original_df, rename_cols, groupby_cols):
    """Helper function to be utilized for create_trailing_game_features."""
    level = len(groupby_cols)
    # this operation forces the index to return to its original value before the transform
    # so that it can be joined to the original dataframe correctly
    window_df = window_df.reset_index().set_index(f'level_{level}').drop(columns=groupby_cols)

    # the rolling stat columns are presently just named the actual stat, so rename them
    # to Trailing Window to reflect that they are trailing stats
    window_df = window_df.rename(columns=rename_cols)

    # rejoin with the original dataframe
    window_df = original_df.merge(window_df, left_index=True, right_index=True)

    assert window_df.shape[0] == original_df.shape[0]
    return window_df


def create_trailing_game_features(window_size, df, features, *rolling_window_function_args,
                                  groupby_cols=['player_id'], min_period=1,
                                  rename_cols={}, rolling_window_function=np.mean, missing_default_value=-999,
                                  **rolling_window_function_kwargs):
    """
    Inputs:
        features: List[str]: list of desired features to get window on (i.e. PTS_PAINT, SPD, SCREEN_AST_PTS, etc.)
        window_size: int: do you want trailing 5 games, trailing 10 games, etc...
        df: pd.DataFrame: inputs containing
            - groupby_col1 
            - groupby_col2
            - groupby_colN
            - window_stats (must be numeric)
            - other_stats
        groupby_cols: List[str]: provide a list of columns to groupby
        missing_default_value: float: For observations that are missing, automatically fill the missing values 
            with this value.
    Outputs:
        pd.DataFrame: contains
            - groupby_col1 
            - groupby_col2
            - groupby_colN
            - Trailing<window_size><window_stat>
            - window_stats
            - other_stats
    """

    # get the rolling average
    window_df = df.groupby(groupby_cols)[features] \
                  .rolling(window=window_size, min_periods=min_period).aggregate(
        rolling_window_function, *rolling_window_function_args, **rolling_window_function_kwargs
    )

    # need to shift by 1 to exclude the current game
    window_df_ex_current = window_df.groupby(groupby_cols).shift(1)

    # check for each column that there's exactly 1 missing entry per player.
    # For some stats this will not be the case as they may not have existed
    # prior to a given year (i.e. if boxouts began getting recorded in 2017
    # then, 2015 boxout stats will show up as null)
    n_players = df.groupby(groupby_cols).head(1).shape[0]
    missing_data = window_df_ex_current[features].isna().sum()
    assert (missing_data == n_players).mean() > 0.5

    # ensure that a player's very first opportunity he has a value of "missing_default_value"..
    # This prevents peaking from occurring in the "not ex_current" columns.
    # if fillna to 0, then it creates a confound with trailing averages that are organically 0.
    window_df_ex_current[features] = window_df_ex_current.fillna(missing_default_value)

    final = _join_window_df_with_original_df(window_df_ex_current, df, rename_cols, groupby_cols)
    return final