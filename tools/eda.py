from pandas_profiling import ProfileReport
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats
from pandas_profiling import ProfileReport

from . import utils as u

def test2():
    print('functions ok')

def get_randomdata(df, n=None, frac=None):
    """ Returns n or a fraction of randomly chosen rows.

    Parameters:
    ----------
    n : int, optional, default=None
        Number of items from axis to return. Cannot be used with `frac`.

    frac : float, optional, default=None
        Fraction of axis items to return. Cannot be used with `n`.

    Returns
    ----------
    df_sample : dataframe

    """
    if n is not None or frac is not None:
        # Randomly sample num_samples elements from dataframe
        df_sample = df.sample(n=n, frac=frac).iloc[:, 1:]
    else:
        df_sample = df.sample(n=100).iloc[:, 1:]
    return df_sample


def get_overview(df, n=None, max_rows=1000):
    """ Returns Pandas Profiling report.

    Parameters:
    ----------
    n : int, default=None
        Number of items from axis to return.

    max_rows : int, default=1000
        Number rows on which the ProfileReport is based.

    Notes
    ----------
    Due to technical limitations, the optimal maximum number of rows on which the report is based is 1000.
    If the actual number of rows is higher than 1000, then the report is constructed on randomly chosen 1000 rows.

    Returns
    ----------
    ProfileReport in html.

    """
    # max_rows = 1000  # the optimal maximum number of rows on which the report is based
    if n is None and df.shape[0] <= max_rows:
        return ProfileReport(df, title='Pandas Profiling Report', minimal=True, html={'style':{'full_width': True}})
    elif n is None and df.shape[0] > max_rows:
        u.log(u.yellow(f"Number of observations is above the benchmark (> {max_rows} rows), "
                    f"extracting overview for {max_rows} random samples..."))
        data = get_randomdata(df, n=max_rows)
        return ProfileReport(data, title='Pandas Profiling Report', minimal=True, html={'style':{'full_width':True}})
    else:
        data = get_randomdata(df, n=n)
        return ProfileReport(data, title='Pandas Profiling Report', minimal=True, html={'style':{'full_width':True}})


def get_summary(df,
                y,
                nan=False,
                formats=False,
                categorical=False,
                min_less_0=False,
                check_normdist=False,
                plot_boxplots=False):
    """Describes the data.

    Parameters:
    ----------
    df : DataFrame
        dataframe on which the summary will be based.

    y : Series
        response variable.

    nan : bool, default=True
        True if need to return a list of NaNs.

    formats : bool, default=True
        True if need to return all the formats of the columns.

    categorical : bool, default=True
        True if need to return values which can be categorical.
        Variable is considered to be categorical if there are less uique values than num_ifcategorical.

    min_less_0 : bool, default=True
        True if need check for variables which have negative values.

    check_normdist : bool, default=True
        True if need check actual distribution against Normal distribution.
        Will make plots of each variable considered against the Normal distribution.

    Returns
    ----------
    A description of the data in text format and plots if check_normdist=True.

    """
    #get numeric data only
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    df_numeric = df.select_dtypes(include=numerics)

    # Checking for NaN
    if nan:
        nans = list(
            pd.DataFrame(df.isna().sum()).rename(columns={0: 'NaNs'}).reset_index().query("NaNs>0")['index'])
        u.log(u.black('NaNs: '), nans)
    else:
        nans = False

    # Checking for unique formats
    if formats:
        unique_formats = list(df.dtypes.unique())
        u.log(u.black('Unique formats: '), unique_formats)
    else:
        formats is False

    # Checking for possible categorical values
    if categorical:
        num_ifcategorical = 10
        possibly_categorical = []
        for col in df.columns:
            set_unique = set(df[col])
            if len(set_unique) <= num_ifcategorical:
                possibly_categorical.append(col)
        u.log(u.black(f'Possible categorical variables (<{num_ifcategorical} unique values): '), possibly_categorical)
    else:
        categorical is False

    # Checking if min value is < 0
    if min_less_0:
        lst_less0 = list(
            pd.DataFrame(df_numeric[df_numeric < 0].any()).rename(columns={0: 'flag'}).query("flag==True").index)
        u.log(u.black(f'Min value < 0: '), lst_less0)
    else:
        min_less_0 is False

    # Plotting actual distributions vs Normal distribution
    def check_distribution(columns, plot_cols=6):
        plt.style.use('seaborn-white')

        if plot_cols > len(df_numeric.columns) - 2:
            # u.log(u.yellow('ERROR: '), f"Can't use more than {len(columns) - 2} columns.")
            plot_cols = len(df_numeric.columns) - 2
            if len(df_numeric.columns) - 2 < 3:
                plot_cols = len(df_numeric.columns)

        # figure size = (width,height)
        f1 = plt.figure(figsize=(30, len(df_numeric.columns) * 3))

        total_plots = len(df_numeric.columns)
        rows = total_plots - plot_cols +1

        for idx, y_var in enumerate(df_numeric.columns):
            if len(set(df_numeric[y_var])) >= 3:
                idx += 1
                ax1 = f1.add_subplot(rows, plot_cols, idx)
                ax1.set_xlabel(y_var)
                sns.distplot(df_numeric[y_var],
                             color='b',
                             hist=False
                             )
                # parameters for normal distribution
                x_min = df_numeric[y_var].min()
                x_max = df_numeric[y_var].max()
                mean = df_numeric[y_var].mean()
                std = df_numeric[y_var].std()
                # plotting normal distribution
                x = np.linspace(x_min, x_max, df_numeric.shape[0])
                y_var = scipy.stats.norm.pdf(x, mean, std)
                plt.plot(x, y_var, color='black', linestyle='dashed')

    if check_normdist:
        u.log(u.black('Plotting distributions of variables against normal distribution'))
        check_distribution(df_numeric.columns, plot_cols=6)


    # Plotting boxplots
    def boxplots(columns, plot_cols=6):
        """
        y - response variable column
        """
        plt.style.use('seaborn-white')

        col_types = ['datetime64[ns]']
        df_selected = df.select_dtypes(exclude=col_types)

        if plot_cols > len(df_selected.columns) - 2:
            # u.log(u.yellow('ERROR: '), f"Can't use more than {len(columns) - 2} columns.")
            plot_cols = len(df_selected.columns) - 2

        # figure size = (width,height)
        f1 = plt.figure(figsize=(30, len(df_selected.columns) * 3))

        total_plots = len(df_selected.columns)
        rows = total_plots - plot_cols

        df_x = df_selected.loc[:, ~df_selected.columns.isin([y.name])]

        for idx, x in enumerate(df_x):
            if len(set(df_selected[x])) >= 3 and (df_selected[x].dtype in numerics or y.dtype in numerics):
                idx += 1
                ax1 = f1.add_subplot(rows, plot_cols, idx)
                sns.boxplot(x=df[x], y=y, data=df_selected)

    if plot_boxplots:
        u.log(u.black('Plotting boxplots'))
        boxplots(df_numeric.columns, plot_cols=6)



