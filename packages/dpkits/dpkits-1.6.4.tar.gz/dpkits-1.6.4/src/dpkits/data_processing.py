import re
import pandas as pd
import numpy as np
from .logging import Logging
from pandas.api.types import CategoricalDtype




class DataProcessing(Logging):

    def __init__(self, *, df_data: pd.DataFrame, df_info: pd.DataFrame):
        super().__init__()
        self.df_data: pd.DataFrame = df_data
        self.df_info: pd.DataFrame = df_info



    @staticmethod
    def str_formater(lst_input: list[str]) -> str:
        return ', '.join(lst_input) if len(lst_input) <= 5 else f"{', '.join(lst_input[:2])},..., {', '.join(lst_input[-2:])}"



    def add_qres(self, dict_add_new_qres: dict, is_add_data_col: bool = True, is_add_info_col: bool = True) -> (pd.DataFrame, pd.DataFrame):
        """
        :param dict_add_new_qres:
            'var_name': ['var_lbl', 'var_type', val_lbl, default value],
            var_name: str
            var_lbl: str
            var_type: str ['SA', 'SA_mtr', 'MA', 'MA_mtr', 'NUM', 'FT']
        :param is_add_data_col: bool
        :param is_add_info_col: bool
        :return: df_data, df_info
        """

        info_col_name = ['var_name', 'var_lbl', 'var_type', 'val_lbl']

        lst_data_addin = list()
        lst_info_addin = list()
        lst_colname = list()
        int_max_row = self.df_data.shape[0]

        for key, val in dict_add_new_qres.items():
            self.print(['Add new variables to df_data & df_info', key], [None, self.clr_blue], sep=': ', end='')

            if val[1] in ['MA']:
                qre_ma_name, max_col = str(key).rsplit('|', 1)

                for i in range(1, int(max_col) + 1):

                    lst_info_addin.append([f'{qre_ma_name}_{i}', val[0], val[1], val[2]])

                    # if '_OE' not in key or is_add_oe_col is True:
                    #     lst_colname.append(f'{qre_ma_name}_{i}')
                    #     lst_data_addin.append([val[-1]] * int_max_row)

                    lst_colname.append(f'{qre_ma_name}_{i}')
                    lst_data_addin.append([val[-1]] * int_max_row)

            else:

                lst_info_addin.append([key, val[0], val[1], val[2]])

                # if '_OE' not in key or is_add_oe_col is True:
                #     lst_colname.append(key)
                #     lst_data_addin.append([val[-1]] * int_max_row)

                lst_colname.append(key)
                lst_data_addin.append([val[-1]] * int_max_row)

            print(end='\r')

        if is_add_info_col:
            self.df_info = pd.concat([self.df_info, pd.DataFrame(columns=info_col_name, data=lst_info_addin)], axis=0, ignore_index=True)

        if is_add_data_col:
            if len(lst_colname) > 0:
                self.df_data = pd.concat([self.df_data, pd.DataFrame(columns=lst_colname, data=np.array(lst_data_addin).transpose())], axis=1)

        self.df_data.reset_index(drop=True, inplace=True)
        self.df_info.reset_index(drop=True, inplace=True)

        self.print(['Add new variables to df_data & df_info: ', self.str_formater(list(dict_add_new_qres.keys())), ' - Completed'], [None, self.clr_blue, None])


        return self.df_data, self.df_info



    def align_ma_values_to_left(self, qre_name: str | list, fillna_val: float = None) -> pd.DataFrame:
        """
        :param qre_name: MA likes 'Q1|8'
        :param fillna_val: fil nan with float value
        :return: df_data
        """
        lst_qre_name = [qre_name] if isinstance(qre_name, str) else qre_name

        for qre_item in lst_qre_name:

            qre, max_col = qre_item.rsplit('|', 1)

            lst_qre = [f'{qre}_{i}' for i in range(1, int(max_col) + 1)]

            df_fil = self.df_data.loc[:, lst_qre].copy()
            df_fil = df_fil.T
            df_sort = pd.DataFrame(np.sort(df_fil.values, axis=0), index=df_fil.index, columns=df_fil.columns)
            df_sort = df_sort.T
            self.df_data[lst_qre] = df_sort[lst_qre]

            del df_fil, df_sort

            if fillna_val:
                self.df_data.loc[self.df_data.eval(f"{qre}_1.isnull()"), f'{qre}_1'] = fillna_val

        self.print(['Align MA values to left: ', self.str_formater(lst_qre_name), ' - Completed'], [None, self.clr_blue, None], end='')
        print(end='\r')


        return self.df_data



    def remove_qres(self, lst_col: list) -> (pd.DataFrame, pd.DataFrame):
        """
        :param lst_col: columns to remove
        :return: df_data, df_info
        """
        self.df_data.drop(columns=lst_col, inplace=True)
        self.df_info = self.df_info.loc[self.df_info.eval(f"~var_name.isin({lst_col})"), :].copy()

        self.df_data.reset_index(drop=True, inplace=True)
        self.df_info.reset_index(drop=True, inplace=True)

        self.print(['Remove questions: ', self.str_formater(lst_col), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data, self.df_info



    def merge_qres(self, *, lst_merge: list, lst_to_merge: list, dk_code: int) -> pd.DataFrame:
        """
        :param lst_merge: output columns
        :param lst_to_merge: input columns
        :param dk_code:
        :return: df_data
        """

        codelist = self.df_info.loc[self.df_info.eval("var_name == @lst_merge[0]"), 'val_lbl'].values.tolist()[0]

        if len(lst_merge) < len(codelist.keys()):
            self.print(f"Merge_qres(error): Length of lst_merge should be greater than or equal length of codelist!!!\nlst_merge = {lst_merge}\ncodelist = {codelist}\nProcessing terminated!!!", self.clr_err)
            exit()


        def merge_row(sr_row: pd.Series, lst_col_name: list, dk: int) -> pd.Series:

            lst_output = sr_row.reset_index(drop=True).drop_duplicates(keep='first').dropna().sort_values().values.tolist()
            output_len = len(lst_col_name)

            if len(lst_output) > 1 and dk in lst_output:
                lst_output.remove(dk)

            if len(lst_output) < output_len:
                lst_output.extend([np.nan] * (output_len - len(lst_output)))

            return pd.Series(data=lst_output, index=lst_col_name)

        self.df_data[lst_merge] = self.df_data[lst_to_merge].apply(merge_row, lst_col_name=lst_merge, dk=dk_code, axis=1)

        self.print(['Merge questions: ', self.str_formater(lst_to_merge), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data



    def convert_percentage(self, lst_qres: list[str], is_check_sum: bool, fil_nan: float = None) -> (pd.DataFrame, pd.DataFrame):
        """
        :param lst_qres: MA likes 'Q1|8'
        :param fil_nan: fill nan value with float
        :param is_check_sum: check sum for share question (these should be 100%)
        :return: df_data, df_info
        """

        df_check_sum = self.df_data['ID']

        for qre in lst_qres:
            self.print(['Convert percentage', qre], [None, self.clr_blue], sep=': ', end='')
            lst_qre = self.convert_ma_pattern(qre) if '|' in qre else [qre]

            self.df_info.loc[self.df_info.eval("var_name.isin(@lst_qre)"), 'var_type'] = 'NUM'
            self.df_data[lst_qre] = self.df_data[lst_qre].replace('%| ', '', regex=True).astype(float)

            if fil_nan is not None:
                self.df_data[lst_qre] = self.df_data[lst_qre].fillna(fil_nan)

            if is_check_sum:
                df_check_sum = pd.concat([df_check_sum, self.df_data[lst_qre].sum(axis=1)], axis=1)
                df_check_sum.rename(columns={0: f'{qre.rsplit('|', 1)[0]}_Sum'}, inplace=True)

            print(end='\r')


        if is_check_sum:
            df_check_sum = df_check_sum.melt(id_vars=['ID']).query("value != 100")

            if not df_check_sum.empty:
                df_check_sum.to_csv('df_check_sum.csv')
                self.print(f"Please check the percentage of ID: \n{df_check_sum} \n saved with 'df_check_sum.csv'", self.clr_err)

        self.print(['Convert percentage: ', self.str_formater(lst_qres), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data, self.df_info



    @staticmethod
    def convert_ma_pattern(str_ma: str) -> list:
        ma_prefix, ma_suffix = str_ma.rsplit('|', 1)
        return [f'{ma_prefix}_{i}' for i in range(1, int(ma_suffix) + 1)]



    @staticmethod
    def update_append_remove(row, method, lst_val_update) -> pd.Series:

        max_len = row.shape[0]
        lst_val = list()

        match method:

            case 'a':
                lst_val = row.dropna().values.tolist()
                lst_val.extend(lst_val_update)
                lst_val = list(dict.fromkeys(lst_val))

            case 'r':
                update_row = row.replace(lst_val_update, np.nan)
                lst_val = update_row.dropna().values.tolist()


        if len(lst_val) != max_len:
            lst_val = lst_val + [np.nan] * (max_len - len(lst_val))

        update_row = pd.Series(index=row.index, data=lst_val)

        return update_row



    def update_qres_data(self, *, query_fil: str, qre_name: str, lst_val_update: list[int | float], method: str) -> pd.DataFrame:
        """
        :param query_fil:
        :param qre_name: MA likes 'Q1|8'
        :param lst_val_update: list[int | float]
        :param method: 'a' = append, 'r' = remove, 'o' = overlay
        :return: df_data
        """

        # Format 'query_fil'--------------------------------------------------------------------------------------------


        # END Format 'query_fil'----------------------------------------------------------------------------------------

        lst_qre_update = self.convert_ma_pattern(qre_name) if '|' in qre_name else [qre_name]

        match method:

            case 'a' | 'r':
                self.df_data.loc[self.df_data.eval(query_fil), lst_qre_update] = self.df_data.loc[self.df_data.eval(query_fil), lst_qre_update].apply(self.update_append_remove, method=method, lst_val_update=lst_val_update, axis=1)

            case 'o':

                if len(lst_qre_update) != len(lst_val_update):
                    self.print("Length of update columns must equal update values!!!!", self.clr_err)
                    return pd.DataFrame()

                else:
                    self.df_data.loc[self.df_data.eval(query_fil), lst_qre_update] = lst_val_update

            case _:
                self.print(f'Please check param method - {method}', self.clr_err)
                return pd.DataFrame()

        self.print(['Update data of questions: ', self.str_formater(lst_qre_update), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data



    def create_count_ma_ranking(self, *, act: str, lst_qre: list) -> (dict, dict):

        dict_add_new_qres = dict()
        dict_data_new_qres = dict()

        def re_ranking(row, ranking_range: int):

            lst_result = [np.nan] * ranking_range

            df = row.to_frame(name='val')
            df['val'] = df['val'].fillna(0)

            df['score'] = list(range(1, df.shape[0] + 1)[::-1])

            for k, v in df.set_index('val', drop=True).to_dict()['score'].items():

                if k == 0:  # ==== Tam sửa ===
                    continue

                lst_result[k - 1] = v

            df['val'] = df['val'].replace({0: np.nan})  # ==== Tam sửa ===

            return lst_result




        for qre in lst_qre:

            match act.upper():

                case 'MA':
                    lst_col_qre = self.df_info.loc[self.df_info.eval(f"var_name.str.contains(r'^{qre}_[\\d]{{1,2}}$') & var_type.isin(['MA', 'MA_mtr'])"), 'var_name'].values.tolist()

                    if not len(lst_col_qre):
                        self.print(f"{qre} is not {act.upper()} questions!!!", self.clr_err)
                        continue

                    new_num_qre = f'{qre}_Count'
                    dict_add_new_qres.update({new_num_qre: [new_num_qre, 'NUM', {}, np.nan]})
                    dict_data_new_qres.update({new_num_qre: self.df_data[lst_col_qre].count(axis=1).values.tolist()})

                case 'RANKING':
                    # lst_col_qre = self.df_info.loc[self.df_info.eval(f"var_name.str.contains(r'^{qre}_Rank[\\d]{{1,2}}$') & var_type.isin(['RANKING'])"), 'var_name'].values.tolist()
                    lst_col_qre = self.df_info.loc[self.df_info.eval(f"var_name.str.contains(r'^{qre}_Rank_[\\d]{{1,2}}$') & var_type.isin(['RANKING'])"), 'var_name'].values.tolist()

                    if not len(lst_col_qre):
                        self.print(f"{qre} is not {act.upper()} questions!!!", self.clr_err)
                        continue

                    dict_codelist = self.df_info.loc[self.df_info.eval("var_name == @lst_col_qre[0]"), 'val_lbl'].values[0]
                    new_num_qre = f'{qre}_ScoreOfAtt'
                    dict_add_new_qres.update(
                        {f"{new_num_qre}_{k}": [f"{k}. {v}", 'NUM', {}, np.nan] for k, v in dict_codelist.items()}
                    )

                    df_ranking: pd.DataFrame = self.df_data[lst_col_qre].apply(re_ranking, ranking_range=len(list(dict_add_new_qres.keys())), axis=1, result_type='expand')
                    df_ranking.columns = list(dict_add_new_qres.keys())
                    dict_data_new_qres = {k: list(v.values()) for k, v in df_ranking.to_dict().items()}

                case _:
                    self.print(f"{act} is not in [MA, RANKING]!!!", self.clr_err)
                    continue

        return dict_add_new_qres, dict_data_new_qres



    def count_ma_choice(self, *, lst_ma_qre: list, dict_replace: dict = None) -> (pd.DataFrame, pd.DataFrame):

        dict_add_new_qres, dict_data_new_qres = self.create_count_ma_ranking(act='MA', lst_qre=lst_ma_qre)

        self.add_qres(dict_add_new_qres)
        self.df_data[list(dict_data_new_qres.keys())] = pd.DataFrame.from_dict(dict_data_new_qres).replace(dict_replace) if dict_replace else pd.DataFrame.from_dict(dict_data_new_qres)

        self.print(['Count MA choice of questions: ', self.str_formater(lst_ma_qre), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data, self.df_info



    def calculate_ranking_score(self, *, lst_ranking_qre: list) -> (pd.DataFrame, pd.DataFrame):

        dict_add_new_qres, dict_data_new_qres = self.create_count_ma_ranking(act='RANKING', lst_qre=lst_ranking_qre)

        self.add_qres(dict_add_new_qres)
        self.df_data[list(dict_data_new_qres.keys())] = pd.DataFrame.from_dict(dict_data_new_qres)

        self.print(['Calculate ranking score of questions: ', self.str_formater(lst_ranking_qre), ' - Completed'], [None, self.clr_blue, None])

        return self.df_data, self.df_info



    def imagery_one_hot_encoding(self, *, dict_encoding: dict) -> (pd.DataFrame, pd.DataFrame):

        id_var = dict_encoding['id_var']
        regex_imagery_col = dict_encoding['regex_imagery_col']
        exclusive_codes = dict_encoding['exclusive_codes']
        lvl1_name = dict_encoding['lvl1_name']
        lvl2_name = dict_encoding['lvl2_name']
        lst_col_img = self.df_data.filter(regex=regex_imagery_col).columns.tolist()


        # generate codelist
        df_info_img: pd.DataFrame = self.df_info.query(f"var_name.str.contains(r'{regex_imagery_col.replace('(', '').replace(')', '')}')")

        df_info_img = df_info_img.replace({'var_name': {regex_imagery_col: r'\1'}}, regex=True)
        df_info_img = df_info_img.replace({'var_lbl': {r'^.+_(.+)$': r'\1'}}, regex=True)

        dict_lvl1_label = {int(k): v for k, v in df_info_img.iloc[0, -1].items()}

        dict_lvl2_label = df_info_img[['var_name', 'var_lbl']].copy().drop_duplicates(keep='first').set_index(keys='var_name', drop=True).to_dict()['var_lbl']
        dict_lvl2_label = {int(k): v for k, v in dict_lvl2_label.items()}


        # generate df_data
        df_melted: pd.DataFrame = self.df_data[[id_var] + lst_col_img].melt(id_vars=[id_var], value_name=lvl1_name, var_name=lvl2_name)

        df_melted[lvl2_name] = df_melted[lvl2_name].str.replace(regex_imagery_col, r'\1', regex=True).astype(int)

        df_melted = df_melted.dropna(subset=[lvl1_name])
        df_melted[lvl1_name] = df_melted[lvl1_name].astype(int).astype('category')
        df_melted = df_melted[~df_melted[lvl1_name].isin(exclusive_codes)]
        df_melted[lvl1_name] = df_melted[lvl1_name].cat.set_categories(list(dict_lvl1_label.keys()), ordered=True)

        df_melted = df_melted.dropna(subset=[lvl2_name])
        df_melted[lvl2_name] = df_melted[lvl2_name].astype(int).astype('category')
        df_melted = df_melted[~df_melted[lvl2_name].isin(exclusive_codes)]
        df_melted[lvl2_name] = df_melted[lvl2_name].cat.set_categories(list(dict_lvl2_label.keys()), ordered=True)

        df_melted['count'] = 1

        df_melted_pivot = df_melted.pivot_table(
            index=[id_var],
            columns=[lvl1_name, lvl2_name],
            values=['count'],
            aggfunc='count',
            fill_value=0,
            dropna=False,
            observed=False,
        )

        df_melted_pivot.columns = df_melted_pivot.columns.droplevel(0)
        flat_col = df_melted_pivot.columns.to_flat_index()

        df_melted_pivot.columns = [f"{lvl1_name}_{int(lvl1)}_{lvl2_name}_{int(lvl2)}" for lvl1, lvl2 in flat_col]

        # generate df_info
        dict_add_qre = dict()

        for colname in df_melted_pivot.columns.tolist():
            lvl1 = re.sub(rf"^{lvl1_name}_(\d+)_{lvl2_name}_(\d+)$", r'\1', colname)
            lvl2 = re.sub(rf"^{lvl1_name}_(\d+)_{lvl2_name}_(\d+)$", r'\2', colname)

            qre_label = colname.replace(f"{lvl1_name}_{int(lvl1)}", dict_lvl1_label[int(lvl1)]).replace(f"{lvl2_name}_{int(lvl2)}", dict_lvl2_label[int(lvl2)])

            dict_add_qre.update({colname: [qre_label, 'SA', {'1': 'Yes', '0': 'No'}, np.nan]})


        self.add_qres(dict_add_qre, is_add_data_col=False)


        # merge df_melted_pivot to df_data
        df_melted_pivot = df_melted_pivot.reset_index(drop=False)
        self.df_data = self.df_data.merge(df_melted_pivot, how='left', on=id_var)


        return self.df_data, self.df_info



    def one_hot_encoding(self, *, dict_one_hot_regex):

        dict_add_qre = dict()

        for key, val in dict_one_hot_regex.items():
            str_prefix = key
            lst_qre_col = self.df_data.filter(regex=val).columns.tolist()
            str_qre_lbl = self.df_info.loc[self.df_info['var_name'].isin(lst_qre_col), 'var_lbl'].values[0]
            dict_cate = self.df_info.loc[self.df_info['var_name'].isin(lst_qre_col), 'val_lbl'].values[0]

            if isinstance(dict_cate, str):
                dict_cate = eval(dict_cate)

            lst_cate_code = [int(k) for k in dict_cate.keys()]

            self.df_data[lst_qre_col] = self.df_data[lst_qre_col].astype(CategoricalDtype(categories=lst_cate_code))

            df_data_one_hot = pd.DataFrame(
                columns=[f"{str_prefix}_{i}" for i in lst_cate_code] + [f"{str_prefix}_nan"],
                index=self.df_data.index,
                data=[[0] * (len(lst_cate_code) + 1)] * self.df_data.shape[0]
            )

            for qre in lst_qre_col:
                df_dummies = pd.get_dummies(self.df_data[qre], prefix=str_prefix, dummy_na=True).astype(int)

                for col in df_dummies.columns:
                    df_data_one_hot[col] += df_dummies[col].values

            df_qre_nan = df_data_one_hot.loc[df_data_one_hot[f'{str_prefix}_nan'] == (len(lst_cate_code) + 1), f'{str_prefix}_nan']

            if not df_qre_nan.empty:
                df_data_one_hot.loc[df_qre_nan.index, :] = [np.nan]

            df_data_one_hot = df_data_one_hot.drop(columns=[f'{str_prefix}_nan'])

            for col in df_data_one_hot.columns:
                cate = str(col).replace(f"{str_prefix}_", '')
                dict_add_qre.update({col: [f"{str_qre_lbl}_{dict_cate[cate]}", 'SA', {'1': 'Yes', '0': 'No'}, np.nan]})


            self.df_data = pd.concat([self.df_data, df_data_one_hot], axis=1)



        self.add_qres(dict_add_qre, is_add_data_col=False)


        return self.df_data, self.df_info

