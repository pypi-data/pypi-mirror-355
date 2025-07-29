from .logging import Logging
from .data_processing import DataProcessing
import pandas as pd
import numpy as np
import pingouin as pg
import prince

from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import KMeans
from kneed import KneeLocator
import matplotlib.pyplot as plt
from tabulate import tabulate

from pydantic import BaseModel, model_validator, field_validator, ConfigDict
from typing import Optional, List, Dict



class PSM(BaseModel):

    class QrePSM(BaseModel):
        too_expensive: str
        expensive: str
        cheap: str
        too_cheap: str

    # input
    str_query: str
    is_remove_outlier: bool = True
    qre_psm: QrePSM

    # output
    model_config = ConfigDict(arbitrary_types_allowed=True)

    df_cumulative: Optional[pd.DataFrame] = None
    opp: Optional[float] = None
    idp: Optional[float] = None
    pmc: Optional[float] = None
    pme: Optional[float] = None




class DataAnalysis(Logging):

    def __init__(self, *, df_data: pd.DataFrame, df_info: pd.DataFrame):
        super().__init__()
        self.df_data = df_data
        self.df_info = df_info



    def penalty_analysis(self, *, dict_define_pen: dict, output_name: str):

        df_pen = pd.DataFrame(
            columns=['Section', 'Qre', 'Label', 'Ma_SP_Lbl', 'GroupCode', 'GroupCode_Pct', 'GroupCode_x_OL_Mean', 'JAR_x_OL_Mean', 'Penalty_Score', 'Pull_Down_Index'],
            data=[]
        )

        df_info = self.df_info.copy()

        for k_sec, v_sec in dict_define_pen.items():
            self.print(['Processing penalty analysis: ', k_sec], [None, self.clr_blue])

            df_data = self.df_data.query(v_sec.get('query')).copy() if v_sec.get('query') else self.df_data.copy()

            for k_sp, v_sp in df_info.loc[df_info.eval(f"var_name == '{v_sec['prod_pre']}'"), 'val_lbl'].values[0].items():

                df_fil = df_data.query(f"{v_sec['prod_pre']}.isin([{k_sp}])")

                for k_jar, v_jar in v_sec['jar_qres'].items():

                    jar_ol_mean = df_fil.loc[df_fil.eval(f"{k_jar}.isin({v_jar['jar']['code']})"), v_sec['ol_qre']].mean()

                    for grp in ['b2b', 't2b']:
                        grp_count = df_fil.loc[df_fil.eval(f"{k_jar}.isin({v_jar[grp]['code']})"), k_jar].count()
                        grp_base = df_fil.loc[df_fil.eval(f"{k_jar}.notnull()"), k_jar].count()

                        if not grp_base:
                            continue


                        grp_pct = grp_count / grp_base
                        grp_ol_mean = df_fil.loc[df_fil.eval(f"{k_jar}.isin({v_jar[grp]['code']})"), v_sec['ol_qre']].mean()
                        pen_score = jar_ol_mean - grp_ol_mean

                        dict_pen_data_row = {
                            'Section': k_sec,
                            'Qre': k_jar,
                            'Label': v_jar['label'],
                            'Ma_SP_Lbl': v_sp,
                            'GroupCode': v_jar[grp]['label'],
                            'GroupCode_Pct': grp_pct,
                            'GroupCode_x_OL_Mean': grp_ol_mean,
                            'JAR_x_OL_Mean': jar_ol_mean,
                            'Penalty_Score': pen_score,
                            'Pull_Down_Index': grp_pct * pen_score,
                        }

                        if df_pen.empty:
                            df_pen = pd.DataFrame(columns=list(dict_pen_data_row.keys()), data=[dict_pen_data_row.values()])
                        else:
                            df_pen = pd.concat([df_pen, pd.DataFrame(columns=list(dict_pen_data_row.keys()), data=[dict_pen_data_row.values()])], axis=0, ignore_index=True)

        with pd.ExcelWriter(f'{output_name}.xlsx', engine='openpyxl') as writer:
            df_pen.to_excel(writer, sheet_name=f'Penalty_Analysis')



    def linear_regression(self, *, dict_define_linear: dict, output_name: str | None, coef_only: bool = False) -> dict:
        """
        :param dict_define_linear: dict like
        {
            'lnr1': {
                'str_query': '',
                'dependent_vars': ['Q1'],
                'explanatory_vars': ['Q4', 'Q5', 'Q9', 'Q6', 'Q10'],
            },
            ...
        }
        :param output_name: *.xlsx | None
        :param coef_only: bool
        :return: dict[dataframe]
        """

        # Single: y = b + a*x
        # Multiple: y = b + a1*x1 + a2*x2 + ... + an*xn

        df_lbl: pd.DataFrame = self.df_info[['var_name', 'var_lbl']].copy()
        df_lbl = df_lbl.set_index(keys='var_name', drop=True)

        for k_lnr, v_lnr in dict_define_linear.items():
            self.print(['Processing linear regression: ', k_lnr], [None, self.clr_blue])

            df_data: pd.DataFrame = self.df_data.query(v_lnr['str_query']).copy() if v_lnr['str_query'] else self.df_data.copy()

            # If data have many dependent_vars, have to calculate mean of its
            df_data['dep_var'] = df_data[v_lnr['dependent_vars']].mean(axis=1)
            df_data = df_data.dropna(subset=['dep_var'], how='any')


            # Standardize predictors
            scaler_X = StandardScaler()
            X_std = scaler_X.fit_transform(df_data[v_lnr['explanatory_vars']])
            X_std = pd.DataFrame(X_std)
            X_std.columns = v_lnr['explanatory_vars']

            scaler_y = StandardScaler()
            y_std = scaler_y.fit_transform(df_data['dep_var'].to_numpy().reshape(-1, 1)).ravel()

            df_linear = pg.linear_regression(y=y_std, X=X_std)

            if coef_only:
                df_linear = df_linear[['names', 'coef']]

            dict_lbl = df_lbl.loc[v_lnr['explanatory_vars'], 'var_lbl'].to_dict()

            df_linear.insert(loc=1, column='label', value=df_linear['names'].replace(dict_lbl))

            v_lnr.update({'df_linear': df_linear})


        if output_name:
            with pd.ExcelWriter(f'{output_name}.xlsx') as writer:
                for k_lnr, v_lnr in dict_define_linear.items():

                    ws_name = f'Lnr Reg-{k_lnr}'
                    v_lnr['df_linear'].to_excel(writer, sheet_name=ws_name, startrow=3)

                    # format excel file

                    wb = writer.book
                    ws = writer.sheets[ws_name]

                    bold = wb.add_format({'bold': True})

                    ws.write('B1', 'Filter', bold)
                    ws.write('B2', 'Dependent Variables', bold)

                    ws.write('C1', v_lnr['str_query'] if v_lnr['str_query'] else 'No filter')
                    ws.write('C2', ', '.join(v_lnr['dependent_vars']))


        return dict_define_linear



    def correlation(self, *, dict_define_corr: dict, output_name: str):
        """
        :param dict_define_corr:
        :param output_name:
        :return: NONE
        """

        with pd.ExcelWriter(f'{output_name}', engine='openpyxl') as writer:
            for key, var in dict_define_corr.items():
                self.print(['Processing correlation: ', key], [None, self.clr_blue])

                df_data = self.df_data.query(var['str_query']).copy() if var['str_query'] else self.df_data.copy()

                # if have many dependent_vars, have to calculate mean of its
                df_data.loc[:, 'dep_var'] = df_data.loc[:, var['dependent_vars']].mean(axis=1)

                x = df_data['dep_var']
                df_corr = pd.DataFrame()


                for i, v in enumerate(var['explanatory_vars']):

                    corr = pg.corr(x, df_data[v])

                    corr['method'] = corr.index
                    corr['x'] = '|'.join(var['dependent_vars'])
                    corr['y'] = v
                    corr.index = [f'correlation {i + 1}']
                    corr = corr[['x', 'y'] + list(corr.columns)[:-2]]

                    df_corr = pd.concat([df_corr, corr])

                df_corr.to_excel(writer, sheet_name=key)



    def key_driver_analysis(self, *, dict_kda: dict, output_name: str | None) -> dict:


        for k_kda, v_kda in dict_kda.items():
            self.print(['Processing KDA: ', k_kda], [None, self.clr_blue])

            df_data: pd.DataFrame = self.df_data.query(v_kda['str_query']) if v_kda['str_query'] else self.df_data.copy()

            df_kda: pd.DataFrame = self.df_info.copy().set_index(keys='var_name', drop=False).loc[v_kda['explanatory_vars'], ['var_name', 'var_lbl']]


            if v_kda['axis_x_dependent_vars']:
                lst_col = v_kda['axis_x_dependent_vars'] + v_kda['axis_y_dependent_vars'] + v_kda['explanatory_vars']

            else:
                lst_col = v_kda['axis_y_dependent_vars'] + v_kda['explanatory_vars']


            df_data = df_data.dropna(subset=lst_col, how='any')

            X = df_data[v_kda['explanatory_vars']]
            scaler_X = StandardScaler()
            X_std = scaler_X.fit_transform(X)

            if v_kda['axis_x_dependent_vars']:

                y1 = df_data[v_kda['axis_x_dependent_vars']].mean(axis=1)
                y2 = df_data[v_kda['axis_y_dependent_vars']].mean(axis=1)

                all_y_std = np.concatenate([y1, y2]).reshape(-1, 1)
                scaler_y = StandardScaler().fit(all_y_std)

                y1_std = scaler_y.transform(y1.to_numpy().reshape(-1, 1)).ravel()
                y2_std = scaler_y.transform(y2.to_numpy().reshape(-1, 1)).ravel()

                model1 = LinearRegression(n_jobs=-1).fit(X_std, y1_std)
                model2 = LinearRegression(n_jobs=-1).fit(X_std, y2_std)

                df_kda['coef_axis_x'] = pd.Series(data=model1.coef_, index=v_kda['explanatory_vars'])
                df_kda['coef_axis_y'] = pd.Series(data=model2.coef_, index=v_kda['explanatory_vars'])

                all_coefs = np.concatenate([df_kda['coef_axis_x'], df_kda['coef_axis_y']]).reshape(-1, 1)

                scaler_coefs = StandardScaler().fit(all_coefs)

                df_kda['coef_axis_x_std'] = pd.Series(data=scaler_coefs.transform(df_kda['coef_axis_x'].to_numpy().reshape(-1, 1)).ravel(), index=v_kda['explanatory_vars'])
                df_kda['coef_axis_y_std'] = pd.Series(data=scaler_coefs.transform(df_kda['coef_axis_y'].to_numpy().reshape(-1, 1)).ravel(), index=v_kda['explanatory_vars'])

            else:

                y2 = df_data[v_kda['axis_y_dependent_vars']].mean(axis=1)
                y2_std = StandardScaler().fit_transform(y2.to_numpy().reshape(-1, 1)).ravel()
                model2 = LinearRegression(n_jobs=-1).fit(X_std, y2_std)

                if v_kda['axis_x_explanatory_vars']:
                    lst_explanatory_vars = v_kda['axis_x_explanatory_vars']

                    df_mean: pd.DataFrame = df_data[lst_explanatory_vars].mean(axis=0)
                    df_mean.index = df_kda.index

                    df_kda['coef_axis_x'] = df_mean

                else:
                    lst_explanatory_vars = v_kda['explanatory_vars']
                    df_kda['coef_axis_x'] = df_data[lst_explanatory_vars].mean(axis=0)

                df_kda['coef_axis_y'] = pd.Series(data=model2.coef_, index=v_kda['explanatory_vars'])
                df_kda['coef_axis_x_std'] = pd.Series(data=StandardScaler().fit_transform(df_kda['coef_axis_x'].to_numpy().reshape(-1, 1)).ravel(), index=v_kda['explanatory_vars'])
                df_kda['coef_axis_y_std'] = pd.Series(data=StandardScaler().fit_transform(df_kda['coef_axis_y'].to_numpy().reshape(-1, 1)).ravel(), index=v_kda['explanatory_vars'])


            v_kda.update({'df_kda': df_kda})



        if output_name:

            with pd.ExcelWriter(f'{output_name}.xlsx') as writer:

                for k_kda, v_kda in dict_kda.items():
                    ws_name = k_kda

                    df_kda: pd.DataFrame = v_kda['df_kda']
                    df_kda = df_kda.reset_index(drop=True)

                    df_kda.to_excel(writer, sheet_name=ws_name, startrow=5)

                    # format excel file
                    wb = writer.book
                    ws = writer.sheets[ws_name]

                    bold = wb.add_format({'bold': True})

                    # KDA information
                    ws.write('B1', 'Filter', bold)
                    ws.write('B2', 'Axis-x dependent variables', bold)
                    ws.write('B3', 'Axis-y dependent variables', bold)

                    ws.write('C1', v_kda['str_query'] if v_kda['str_query'] else 'No filter')
                    ws.write('C2', ', '.join(v_kda['axis_x_dependent_vars']) if v_kda['axis_x_dependent_vars'] else (f"Mean of: {', '.join(v_kda['axis_x_explanatory_vars'])}" if v_kda['axis_x_explanatory_vars'] else 'Mean of Imagery Factors'))
                    ws.write('C3', ', '.join(v_kda['axis_y_dependent_vars']))


                    # Chart Plotting

                    # Build the scatter chart
                    chart = wb.add_chart({
                        'type': 'scatter',
                        'subtype': 'marker_only',
                    })

                    # 3.1 Define the data range for the chart:
                    #     categories = coef_axis_x  (column B, zero-based col 1)
                    #     values     = coef_axis_y  (column C, zero-based col 2)

                    max_row = len(df_kda) + 5  # number of data rows

                    for idx, irow in enumerate(range(6, max_row)):
                        chart.add_series({
                            # 'name': df_kda.at[idx, 'var_lbl'],
                            'name': [ws_name, irow, 2, irow, 2],
                            'categories': [ws_name, irow, 5, irow, 5],
                            'values': [ws_name, irow, 6, irow, 6],
                            'marker': {'type': 'circle', 'size': 5},
                            'data_labels': {
                                'series_name': True,  # ← show the series name
                                'position': 'above'  # e.g. 'above','below','left','right','center'
                            }
                        })

                    # 3.2 Format the axes
                    str_x_axis_name = f"Derived importance ({', '.join(v_kda['axis_x_dependent_vars'])})" if v_kda['axis_x_dependent_vars'] else 'Stated importance'

                    chart.set_x_axis(
                        {
                            'name': str_x_axis_name,
                            'major_gridlines': {'visible': False},
                            'min': -3,
                            'max': 3,
                            'major_unit': 1,
                            'crossing': -3,
                        }
                    )

                    chart.set_y_axis(
                        {
                            'name': f"Derived importance ({', '.join(v_kda['axis_y_dependent_vars'])})",
                            'major_gridlines': {'visible': False},
                            'min': -3,
                            'max': 3,
                            'major_unit': 1,
                            'crossing': -3,
                        }
                    )

                    chart.set_title({'name': ws_name})
                    chart.set_style(10)

                    chart.set_legend({'position': 'none'})

                    chart.set_size({
                        'width': 1000,
                        'height': 600,
                    })


                    ws.insert_chart('I2', chart)

                    self.print(['Chart inserted: ', ws_name], [None, self.clr_blue])


        return dict_kda



    def correspondence_analysis(self, *, dict_ca: dict, output_name: str | None) -> dict:

        for k_ca, v_ca in dict_ca.items():

            df_ca: pd.DataFrame = self.df_data.query(v_ca['str_query']) if v_ca['str_query'] else self.df_data.copy()
            df_info: pd.DataFrame = self.df_info.copy()
            df_info = df_info.set_index(keys=['var_name'], drop=False)

            lst_col_ca = [v_ca['id_var'], v_ca['brand_var']] + v_ca['imagery_vars']

            df_ca = df_ca[lst_col_ca].melt(id_vars=[v_ca['id_var'], v_ca['brand_var']])
            df_ca = df_ca.loc[df_ca['value'] == 1, :]

            dict_brandlist = {int(k): v for k, v in df_info.loc[v_ca['brand_var'], 'val_lbl'].items()}
            df_ca[v_ca['brand_var']] = df_ca[v_ca['brand_var']].astype(int).replace(dict_brandlist)

            dict_img_list = df_info.loc[v_ca['imagery_vars'], 'var_lbl'].to_dict()
            df_ca['variable'] = df_ca['variable'].replace(dict_img_list)

            df_contingency = df_ca.pivot_table(
                index=['variable'],
                columns=[v_ca['brand_var']],
                values=['value'],
                fill_value=0,
                aggfunc='count'
            )

            df_contingency.columns = df_contingency.columns.droplevel(0)

            mdl_ca = prince.CA(
                # n_components=2,      # number of dimensions to keep
                n_iter=20,           # number of power-iterations
                # copy=True,           # leave the original table intact
                # check_input=True,
                # engine='sklearn',
                random_state=42
            ).fit(df_contingency)






            # Row (IMAGERY) coordinates
            df_coords_row = mdl_ca.row_coordinates(df_contingency)
            df_coords_row['Type'] = 'IMAGERY'
            df_coords_row['Nearest_Point'] = ''
            df_coords_row.index.name = 'Index'


            # Column (BRAND) coordinates
            df_coords_col = mdl_ca.column_coordinates(df_contingency)
            df_coords_col['Type'] = 'BRAND'
            df_coords_row['Nearest_Point'] = ''
            df_coords_col.index.name = 'Index'

            for brand in df_coords_col.index.tolist():
                brand_coord = df_coords_col.loc[brand, [0, 1]].values.reshape(1, -1)

                distances = euclidean_distances(brand_coord, df_coords_row[[0, 1]])[0]

                # Create a Series of distances with index
                distance_series = pd.Series(distances, index=df_coords_row.index)

                # Exclude itself, then get top 3 nearest
                # nearest_points = distance_series.drop(brand).nsmallest(3)
                nearest_points = distance_series.nsmallest(3)

                df_coords_row.loc[nearest_points.index, 'Nearest_Point'] += f"|{brand}"


            df_coords_row = df_coords_row.reset_index(drop=False)
            df_coords_col = df_coords_col.reset_index(drop=False)

            v_ca.update({
                'df_ca': df_ca,
                'df_contingency': df_contingency,
                'df_coords': pd.concat([df_coords_col, df_coords_row], axis=0).rename(columns={0: 'Axis-x', 1: 'Axis-y'}),
            })




        if output_name:

            with pd.ExcelWriter(f'{output_name}.xlsx') as writer:

                for k_ca, v_ca in dict_ca.items():
                    ws_name = k_ca

                    # v_ca['df_ca'].to_excel(writer, sheet_name=f"{ws_name}-df_ca")
                    # v_ca['df_contingency'].to_excel(writer, sheet_name=f"{ws_name}-df_con")

                    df_coords: pd.DataFrame = v_ca['df_coords']
                    df_coords = df_coords.reset_index(drop=True)

                    df_coords.to_excel(writer, sheet_name=ws_name, startrow=5)

                    # format excel file
                    wb = writer.book
                    ws = writer.sheets[ws_name]

                    bold = wb.add_format({'bold': True})

                    # CA information
                    ws.write('B1', 'Filter', bold)
                    ws.write('C1', v_ca['str_query'] if v_ca['str_query'] else 'No filter')


                    # Chart Plotting

                    # Build the scatter chart
                    chart = wb.add_chart({
                        'type': 'scatter',
                        'subtype': 'marker_only',
                    })

                    max_row = len(df_coords) + 5  # number of data rows

                    for idx, irow in enumerate(range(6, max_row)):
                        chart.add_series({
                            'name': [ws_name, irow, 1, irow, 1],
                            'categories': [ws_name, irow, 2, irow, 2],
                            'values': [ws_name, irow, 3, irow, 3],

                            'marker': {'type': 'diamond', 'size': 8} if df_coords.at[idx, 'Type'] == 'BRAND' else {'type': 'circle', 'size': 5},

                            'data_labels': {
                                'series_name': True if len(str(df_coords.at[idx, 'Nearest_Point'])) else False,  # ← show the series name
                                # 'series_name': True,  # ← show the series name
                                'position': 'above'  # e.g. 'above','below','left','right','center'
                            }
                        })


                    chart.set_title({'name': ws_name})
                    chart.set_style(10)

                    chart.set_legend({'position': 'none'})

                    chart.set_x_axis(
                        {
                            # 'name': ,
                            'major_gridlines': {'visible': False},
                        }
                    )

                    chart.set_y_axis(
                        {
                            # 'name': ,
                            'major_gridlines': {'visible': False},
                        }
                    )


                    chart.set_size({
                        'width': 1000,
                        'height': 600,
                    })

                    ws.insert_chart('H2', chart)

                    self.print(['Chart inserted: ', ws_name], [None, self.clr_blue])



        return dict_ca



    def price_sensitive_metric(self, *, dict_psm: dict, output_name: str | None) -> dict:


        for k_psm, psm in dict_psm.items():

            psm = PSM(**psm)
            dict_psm[k_psm] = psm

            df_data_psm: pd.DataFrame = self.df_data.loc[self.df_data.eval(psm.str_query), psm.qre_psm.model_dump().values()] if psm.str_query else self.df_data.loc[:, psm.qre_psm.model_dump().values()]

            df_data_psm = df_data_psm.rename(columns={old: new for new, old in psm.qre_psm.model_dump().items()})

            lst_price_col = psm.qre_psm.model_dump().keys()

            # Filter out logically impossible answers
            df_err = df_data_psm.query("~(too_expensive > expensive > cheap > too_cheap)")

            if not df_err.empty:
                self.print(["Please check invalid values: \n", tabulate(df_err, headers='keys', tablefmt='pretty')], [self.clr_err, self.clr_err])
                return dict()

            # ------------------------------------------------------------------
            # 1)  Structural filter  (answers must be strictly ascending)
            # ------------------------------------------------------------------
            cols = ["too_cheap", "cheap", "expensive", "too_expensive"]
            df_data_psm = df_data_psm[df_data_psm[cols].apply(lambda r: r.is_monotonic_increasing, axis=1)]


            # ------------------------------------------------------------------
            # 2)  Tukey IQR trim  (drops obvious outliers)
            # ------------------------------------------------------------------
            if psm.is_remove_outlier:
                df_data_psm['is_remove'] = False

                def remove_outlier(row: pd.Series) -> pd.Series:

                    # “Tukey IQR fence”

                    for col in lst_price_col:

                        q1, q3 = df_data_psm[col].quantile([0.25, 0.75])
                        iqr = q3 - q1
                        k = 1.5
                        min_price, max_price = (q1 - k * iqr), (q3 + k * iqr)

                        if not (min_price <= row[col] <= max_price):
                            row['is_remove'] = True

                    return row

                df_data_psm = df_data_psm.apply(remove_outlier, axis=1)

                df_outlier: pd.DataFrame = df_data_psm.loc[df_data_psm['is_remove']]

                if df_outlier.empty:
                    self.print("No outlier was detected", self.clr_succ)

                else:
                    self.print([f"PSM({k_psm}) - Detect and remove {df_outlier.shape[0]} rows which contain outlier values"], [self.clr_warn])
                    df_data_psm = df_data_psm.loc[~df_data_psm['is_remove']]

                df_data_psm = df_data_psm.drop(columns=['is_remove'])

            else:

                self.print(f"You don't remove outlier in PSM({k_psm})", self.clr_warn)


            df_cumulative: pd.DataFrame = df_data_psm.melt()
            df_cumulative['count'] = 1
            df_cumulative = pd.pivot_table(
                df_cumulative,
                index='value',
                columns='variable',
                values='count',
                aggfunc='count',
                fill_value=0,
            )

            df_cumulative = df_cumulative[lst_price_col].apply(lambda x: x.div(x.sum())).cumsum()
            df_cumulative[['cheap', 'too_cheap']] = [1, 1] - df_cumulative[['cheap', 'too_cheap']]

            df_cumulative = df_cumulative.reset_index(drop=False).rename(columns={'value': 'price'})

            df_cumulative["opp_diff"] = df_cumulative["too_cheap"] - df_cumulative["too_expensive"]
            df_cumulative["idp_diff"] = df_cumulative["cheap"] - df_cumulative["expensive"]
            df_cumulative["pmc_diff"] = df_cumulative["too_cheap"] - df_cumulative["expensive"]
            df_cumulative["pme_diff"] = df_cumulative["cheap"] - df_cumulative["too_expensive"]

            def first_sign_change(diff):
                sign = np.sign(diff)
                flips = np.where(np.diff(sign) != 0)[0]  # indices BEFORE the flip
                return flips[0] if len(flips) else None


            def interpolate_cross(x, y):
                i = first_sign_change(y)

                if i is None:  # no crossing
                    return None

                x1, x2 = x[i], x[i + 1]
                y1, y2 = y[i], y[i + 1]
                return x1 - y1 * (x2 - x1) / (y2 - y1)  # straight‑line interpolation

            psm.opp = interpolate_cross(df_cumulative["price"], df_cumulative["opp_diff"])
            psm.idp = interpolate_cross(df_cumulative["price"], df_cumulative["idp_diff"])
            psm.pmc = interpolate_cross(df_cumulative["price"], df_cumulative["pmc_diff"])
            psm.pme = interpolate_cross(df_cumulative["price"], df_cumulative["pme_diff"])

            df_cumulative = df_cumulative.drop(columns=['opp_diff', 'idp_diff', 'pmc_diff', 'pme_diff'])

            psm.df_cumulative = df_cumulative

            print('Section:', k_psm)
            print('    - Optimal Price Point (OPP):', psm.opp)
            print('    - Indifference Price Point (IDP):', psm.idp)
            print('    - Point of Marginal Cheapness (PMC):', psm.pmc)
            print('    - Point of Marginal Expensiveness (PME):', psm.pme)


        print("Exporting xlsx file")

        if output_name:
            # export file & chart

            with pd.ExcelWriter(f'{output_name}.xlsx') as writer:

                for k_psm, psm in dict_psm.items():

                    ws_name = k_psm

                    df_cumulative: pd.DataFrame = psm.df_cumulative
                    df_cumulative.to_excel(writer, sheet_name=ws_name, startrow=5)

                    # format excel file
                    wb = writer.book
                    ws = writer.sheets[ws_name]
                    bold = wb.add_format({'bold': True})
                    price_fmt = wb.add_format({'num_format': '#,##0'})
                    pct_fmt = wb.add_format({'num_format': '0.00%'})

                    # PSM information
                    ws.write('B1', 'Filter', bold)
                    ws.write('B2', 'Optimal Price Point (OPP)', bold)
                    ws.write('B3', 'Indifference Price Point (IDP)', bold)
                    ws.write('B4', 'Point of Marginal Cheapness (PMC)', bold)
                    ws.write('B5', 'Point of Marginal Expensiveness (PME)', bold)

                    ws.write('C1', psm.str_query if psm.str_query else 'No filter')
                    ws.write('C2', psm.opp, price_fmt)
                    ws.write('C3', psm.idp, price_fmt)
                    ws.write('C4', psm.pmc, price_fmt)
                    ws.write('C5', psm.pme, price_fmt)



                    # 2) apply them to whole columns:
                    ws.set_column(0, 0, 3)
                    #    column 1 (Price), width=12
                    ws.set_column(1, 1, 35, price_fmt)

                    #    columns 2–5 (your proportions), width=10
                    ws.set_column(2, 2, 14, pct_fmt)
                    ws.set_column(3, 5, 12, pct_fmt)


                    # Chart Plotting

                    # Build the scatter chart
                    chart = wb.add_chart({
                        'type': 'line',
                        # 'subtype': 'marker_only',
                    })

                    max_row = len(df_cumulative) + 5  # number of data rows

                    for icol in range(2, 6):
                        chart.add_series({
                            'name': [ws_name, 5, icol, 5, icol],
                            'categories': [ws_name, 6, 1, max_row, 1],
                            'values': [ws_name, 6, icol, max_row, icol],
                            # 'marker': {'type': 'automatic'},
                            'line': {'width': 2},
                        })


                    chart.set_title({'name': ws_name})
                    chart.set_style(10)

                    chart.set_legend({'position': 'bottom'})

                    chart.set_size({
                        'width': 1000,
                        'height': 600,
                    })

                    ws.insert_chart('H2', chart)

                    self.print(['Chart inserted: ', ws_name], [None, self.clr_blue])


        return dict_psm



    def k_mean_segmentation(self, *, dict_k_mean: dict, output_name: str | None) -> (pd.DataFrame, pd.DataFrame):

        dp = DataProcessing(df_data=self.df_data, df_info=self.df_info)

        for key, val in dict_k_mean.items():
            df_data: pd.DataFrame = self.df_data.query(val['str_query']) if val['str_query'] else self.df_data.copy()

            df_data = df_data.loc[:, val['lst_qre']].fillna(0)

            normalizer = Normalizer()
            df_data_norm: pd.DataFrame = normalizer.fit_transform(df_data)

            if val['n_clusters'] == 'auto':

                K = range(2, 9)
                wcss = list()

                for k in K:
                    # train the model for current value of k on training data
                    model = KMeans(n_clusters=k, random_state=0).fit(df_data_norm)

                    # Append the within-cluster sum of square to wcss
                    wcss.append(model.inertia_)


                kl = KneeLocator(K, wcss, curve='convex', direction='decreasing')
                n_clusters = kl.knee
                self.print([f"Optimal k by knee detection: {n_clusters}"], [self.clr_blue])

                plt.plot(K, wcss, 'bx-')
                plt.xlabel('Number of clusters k')
                plt.ylabel('WCSS (inertia)')
                plt.title('Elbow Method for Optimal k')
                plt.show()

            else:
                n_clusters = int(val['n_clusters'])
                self.print([f"Selected n_clusters: {n_clusters}"], [self.clr_blue])

            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans.fit(df_data_norm)

            dict_add_new_qres = {
                key: [f'{key}: k-mean', 'SA', {i: f'Cluster {i}' for i in range(1, n_clusters + 1)}, np.nan]
            }

            dp.add_qres(dict_add_new_qres)
            self.df_data, self.df_info = dp.df_data, dp.df_info

            self.df_data[key] = kmeans.labels_ + 1


        if output_name:
            self.print(["Export excel file: ", output_name], [None, self.clr_blue])

            with pd.ExcelWriter(f'{output_name}') as writer:
                self.df_data.to_excel(writer, sheet_name='df_data-k-mean')
                self.df_info.to_excel(writer, sheet_name='df_info-k-mean')


        return self.df_data, self.df_info








    # MORE ANALYSIS HERE







