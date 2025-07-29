import pandas as pd
import numpy as np
import time
import datetime
import math
import multiprocessing
import traceback
import warnings
from scipy import stats
from .logging import Logging




class DataTableGeneratorV2(Logging):

    def __init__(self, *, df_data: pd.DataFrame, df_info: pd.DataFrame, xlsx_name: str, is_md: bool = False, dict_df_tables: dict = None, is_validate_data: bool = True):

        super().__init__()

        pd.set_option('future.no_silent_downcasting', True)

        self.is_md = is_md

        self.df_data, self.df_info = self.convert_md_to_mc(df_data=df_data, df_info=df_info) if is_md else df_data, df_info

        self.file_name = xlsx_name.rsplit('/', 1)[-1] if '/' in xlsx_name else xlsx_name

        self.dict_df_tables = dict_df_tables if dict_df_tables else dict()

        # Check file permission-----------------------------------------------------------------------------------------
        try:
            check_perm = open(xlsx_name)
            check_perm.close()

        except PermissionError:
            self.print(f'Permission Error when access file: {xlsx_name}, Processing terminated.', self.clr_err)
            exit()
        except FileNotFoundError:
            pass


        # Unnetted value label------------------------------------------------------------------------------------------
        self.df_info['val_lbl'] = self.df_info['val_lbl'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        self.df_info['val_lbl_unnetted'] = self.df_info['val_lbl']
        self.df_info = self.unnetted_qre_val(df_info=self.df_info)


        if is_validate_data:

            # Check matching of data và defines-------------------------------------------------------------------------
            tpl_err = self.valcheck_strange_values(df_data=self.df_data, df_info=self.df_info)

            if not tpl_err[0]:
                self.print(tpl_err[1], self.clr_err)
                exit()
            else:
                self.print(tpl_err[1])

            # Remove duplicate value of MA qres-------------------------------------------------------------------------
            self.df_data = self.valcheck_remove_duplicate_ma_vars_values(df_data=self.df_data, df_info=self.df_info)






    def unnetted_qre_val(self, *, df_info: pd.DataFrame) -> pd.DataFrame:

        def unnetted_val(dict_netted: dict) -> dict:

            dict_unnetted = dict()

            if 'net_code' not in dict_netted.keys():
                return dict_netted

            for key, val in dict_netted.items():

                if 'net_code' in key:
                    val_lbl_lv1 = dict_netted['net_code']

                    for net_key, net_val in val_lbl_lv1.items():

                        if isinstance(net_val, str):
                            dict_unnetted.update({str(net_key): net_val})
                        else:
                            self.print(f"Unnetted {net_key}", self.clr_magenta)
                            dict_unnetted.update(net_val)

                else:
                    dict_unnetted.update({str(key): val})


            return dict_unnetted

        df_val_lbl = df_info[['var_name', 'val_lbl']].astype(str).query("val_lbl.str.contains('net_code')")

        if df_val_lbl.empty:
            self.print(['No Netted in value label', 'Skipped'], [None, self.clr_succ], sep=' - ')
            return df_info

        val_a = str()
        val_b = dict()
        for idx in df_val_lbl.index:

            if val_a != str(df_info.at[idx, 'val_lbl_unnetted']):
                val_a = str(df_info.at[idx, 'val_lbl_unnetted'])
                val_b = unnetted_val(eval(df_val_lbl.at[idx, 'val_lbl']))

            df_info.at[idx, 'val_lbl_unnetted'] = val_b

        self.print('Unnetted value label - Completed')

        return df_info



    @staticmethod
    def convert_md_to_mc(*, df_data: pd.DataFrame, df_info: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):

        df_info_qre_ma_all_1st_col = df_info.query("var_type.isin(['MA', 'MA_mtr']) & var_name.str.contains('[A-Za-z]+_1$')").copy()

        for idx in df_info_qre_ma_all_1st_col.index:
            qre = df_info_qre_ma_all_1st_col.at[idx, 'var_name'].rsplit('_', 1)[0]

            df_info_ma = df_info.query(f"var_name.str.contains('^{qre}_[0-9]+$')").copy()

            dict_val_lbl = dict()
            for idx_ma in df_info_ma.index:
                str_qre, str_val = str(df_info_ma.at[idx_ma, 'var_name']).rsplit('_', 1)
                dict_val_lbl[str_val] = df_info_ma.at[idx_ma, 'val_lbl']['1']

                df_data[df_info_ma.at[idx_ma, 'var_name']] = df_data[df_info_ma.at[idx_ma, 'var_name']].replace({1: int(str_val)})

            df_info.loc[df_info_ma.index,  ['val_lbl']] = [dict_val_lbl]

            lst_ma_col_name = df_info_ma['var_name'].values.tolist()

            df_data[lst_ma_col_name[0]] = df_data[lst_ma_col_name].values.tolist()

            for idx_dt in df_data.index:
                arr = np.sort(df_data.at[idx_dt, lst_ma_col_name[0]], axis=None)
                df_data.at[idx_dt, lst_ma_col_name[0]] = arr

            df_data[lst_ma_col_name] = pd.DataFrame(df_data[lst_ma_col_name[0]].tolist(), index=df_data.index)

        return df_data, df_info



    @staticmethod
    def valcheck_strange_values(*, df_data: pd.DataFrame, df_info: pd.DataFrame) -> (bool, str):

        df_info = df_info.set_index('var_name')
        df_info = df_info.loc[df_info.eval("~var_type.isin(['FT', 'FT_mtr', 'NUM']) | var_name == 'ID'"), :].drop(columns=['var_lbl', 'var_type', 'val_lbl'])

        for idx in df_info.index:
            if idx == 'ID':
                continue

            val_lbl_unnetted = eval(df_info.at[idx, 'val_lbl_unnetted']) if isinstance(df_info.at[idx, 'val_lbl_unnetted'], str) else df_info.at[idx, 'val_lbl_unnetted']

            df_info.at[idx, 'val_lbl_unnetted'] = {int(k): np.nan for k in val_lbl_unnetted.keys()}


        dict_replace = df_info.to_dict()['val_lbl_unnetted']
        dict_replace.pop('ID')

        df_data = df_data.loc[:, df_info.index].replace(dict_replace).dropna(how='all').dropna(axis=1, how='all')

        df_data = pd.DataFrame(df_data)

        df_data = df_data.reset_index(drop=True if 'ID' in df_data.columns else False)


        df_data = pd.melt(df_data, id_vars=df_data.columns[0], value_vars=df_data.columns[1:]).dropna()

        if not df_data.empty:
            return False, f'Please check values not in codelist:\n{df_data.to_string()}'

        return True, "Check strange values: df_data vs df_info -> Completed"



    def valcheck_remove_duplicate_ma_vars_values(self, df_data: pd.DataFrame, df_info: pd.DataFrame) -> pd.DataFrame:

        # # # REMOVING DUPLICATED VALUES--------------------------------------------------------------------------------
        str_query = "var_name.str.contains(r'^\\w+_1$') & var_type.str.contains('MA')"
        df_info_ma = df_info.query(str_query)

        def remove_dup(row: pd.Series):
            row_idx = row.index.values.tolist()
            lst_val = row.drop_duplicates(keep='first').values.tolist()
            return lst_val + ([np.nan] * (len(row_idx) - len(lst_val)))

        for qre_ma in df_info_ma['var_name'].values.tolist():
            prefix, suffix = qre_ma.rsplit('_', 1)

            self.print(f"Remove duplicate MA qres' values - {prefix}", end='')

            cols = df_info.loc[df_info.eval(f"var_name.str.contains('^{prefix}_[0-9]{{1,2}}$')"), 'var_name'].values.tolist()
            df_data[cols] = df_data[cols].apply(remove_dup, axis=1, result_type='expand')

            print(end='\r')


        self.print("Remove duplicate MA qres' values - Completed")

        return df_data



    def valcheck_header_level(self, *, dict_tables: dict):

        is_err = False

        for key, val in dict_tables.items():

            if len(val['dict_header_qres']) == 1:
                continue

            prev_len = -1
            for sub_key, sub_val in val['dict_header_qres'].items():
                if prev_len == -1:
                    prev_len = len(sub_val)
                    continue

                if prev_len != len(sub_val):
                    self.print(f'Table {key} has invalid header and process is terminated', self.clr_err)
                    is_err = True

        if is_err:
            exit()

        self.print('Validate header - Completed')



    def run_tables(self, *, lst_group_tables: list):

        st = time.time()

        lst_run_table = list(self.dict_df_tables.keys())

        for group in lst_group_tables:

            if not group['tables_to_run']:
                self.print('No selected tables. Processing terminated!!!', self.clr_err)
                exit()

            dict_tables = {k: v for k, v in group['tables_format'].items() if k in group['tables_to_run']}

            for tbl_key, tbl_val in dict_tables.items():
                if tbl_val.get('weight_var') and tbl_val.get('sig_test_info').get('sig_type'):
                    self.print(f'Cannot run table "{tbl_key}" with significant test and weighting at the same time. Processing terminated!!!', self.clr_err)
                    exit()

            lst_run_table.extend(group['tables_to_run'])

            self.generate_tables_by_group(dict_tables=dict_tables, lst_run_table=lst_run_table)

        self.print(f">>> Table(s) generation have completed in {datetime.timedelta(seconds=time.time() - st)}", self.clr_succ)



    def generate_tables_by_group(self, *, dict_tables: dict, lst_run_table: list):

        self.valcheck_header_level(dict_tables=dict_tables)


        def detect_debugger():
            for frame in traceback.extract_stack():
                if 'pydevd' in frame.filename.lower():
                    return True
            return False

        if detect_debugger():
            is_multiple_process = False

        else:
            is_multiple_process = True


        # # # FOR TESTING--------------------------------
        # is_multiple_process = True
        is_new_way = False
        # # # FOR TESTING--------------------------------


        lst_processed_tables = list()

        match is_multiple_process:

            case True:

                # MULTIPLE PROCESSING-----------------------------------------------------------------------------------
                num_cores = multiprocessing.cpu_count()
                num_cores_processing = num_cores - 1

                self.print(f'>>> Number of CPU cores to be used for multiple processing: {num_cores_processing} / {num_cores}', self.clr_warn)

                pool = multiprocessing.Pool(processes=num_cores_processing)

                # Map tasks to the worker function
                lst_processed_tables = pool.map(self.run_standard_table_sig, list(dict_tables.values()))

                # Close and join the pool
                pool.close()
                pool.join()
                # End MULTIPLE PROCESSING-------------------------------------------------------------------------------

            case False:

                self.print('>>> Single processing', self.clr_warn)

                for item in list(dict_tables.values()):

                    if not is_new_way:
                        lst_processed_tables.append(self.run_standard_table_sig(item))

                    else:
                        # new way processing
                        lst_processed_tables.append(self.generate_table(dict_table=item))


        self.dict_df_tables.update({arr[0]: arr[-1] for arr in lst_processed_tables})
        self.dict_df_tables = dict(sorted(self.dict_df_tables.items(), key=lambda iitem: lst_run_table.index(iitem[0])))

        with pd.ExcelWriter(self.file_name, engine='xlsxwriter') as writer:
            pd.DataFrame(columns=['#', 'Content'], data=[]).to_excel(writer, sheet_name='Content', index=False)

            for k, v in self.dict_df_tables.items():
                v.to_excel(writer, sheet_name=k, index=False)
                self.print(['Save table', k, ' Completed'], [None, self.clr_blue, None], sep=' | ')







    # OLD---------------------------------------------------------------------------------------------------------------


    def convert_table_header_to_list(self, lst_header_qres: list) -> list:

        df_info = self.df_info.copy()


        def get_cats_by_qre_name(qre_name: str) -> dict:
            str_qre_name = f'{qre_name[1:]}_1' if '$' in qre_name else qre_name
            return df_info.loc[df_info.eval(f"var_name == '{str_qre_name}'"), 'val_lbl'].values[0]


        def group_sig_table_header_query(dict_qre: dict, str_cat_or_query) -> str:

            if '$' in dict_qre['qre_name']:

                if 'RANK' in str(dict_qre['qre_name']).upper():
                    # lst_qre_ma_name = df_info.query(f"var_name.str.contains('^{dict_qre['qre_name'][1:]}[0-9]+$')")['var_name'].values.tolist()
                    lst_qre_ma_name = df_info.query(f"var_name.str.contains('^{dict_qre['qre_name'][1:]}_[0-9]+$')")['var_name'].values.tolist()
                else:
                    lst_qre_ma_name = df_info.query(f"var_name.str.contains('^{dict_qre['qre_name'][1:]}_[0-9]+$')")['var_name'].values.tolist()

                if str(str_cat_or_query).upper() == 'TOTAL':
                    return f"({' | '.join([f'{i} > 0' for i in lst_qre_ma_name])})"

                return f"({' | '.join([f'{i} == {str_cat_or_query}' for i in lst_qre_ma_name])})"


            if str(str_cat_or_query).upper() == 'TOTAL':
                return f"{dict_qre['qre_name']} > 0"

            if '@' in dict_qre['qre_name']:
                return str_cat_or_query

            return f"{dict_qre['qre_name']} == {str_cat_or_query}"



        lst_group_header = list()

        while len(lst_header_qres) != 5:
            lst_header_qres.append([])

        lvl1, lvl2, lvl3, lvl4, lvl5 = lst_header_qres

        for a in lvl1:

            if not a['cats']:
                a['cats'] = get_cats_by_qre_name(a['qre_name'])

            if not lvl2:
                dict_grp_hd = dict()
                dict_idx = {list(a['cats'].keys())[i]: i for i in range(len(a['cats'].keys()))}

                for a_k, a_v in a['cats'].items():
                    # qa = f"{a['qre_name']} > 0" if str(a_k).upper() == 'TOTAL' else (a_k if '@' in a['qre_name'] else f"{a['qre_name']} == {a_k}")
                    qa = group_sig_table_header_query(a, a_k)

                    dict_grp_hd.update({
                        dict_idx[a_k]: {
                            "lbl": f"{a['qre_lbl']}@{a_v}",
                            "query": f"{qa}"
                        }
                    })

                lst_group_header.append(dict_grp_hd)
                continue

            for a_k, a_v in a['cats'].items():
                # qa = f"{a['qre_name']} > 0" if str(a_k).upper() == 'TOTAL' else (a_k if '@' in a['qre_name'] else f"{a['qre_name']} == {a_k}")
                qa = group_sig_table_header_query(a, a_k)

                for b in lvl2:

                    if not b['cats']:
                        b['cats'] = get_cats_by_qre_name(b['qre_name'])

                    if not lvl3:
                        dict_grp_hd = dict()
                        dict_idx = {list(b['cats'].keys())[i]: i for i in range(len(b['cats'].keys()))}

                        for b_k, b_v in b['cats'].items():
                            # qb = f"{b['qre_name']} > 0" if str(b_k).upper() == 'TOTAL' else f"{b['qre_name']} == {b_k}"
                            qb = group_sig_table_header_query(b, b_k)

                            dict_grp_hd.update({
                                dict_idx[b_k]: {
                                    "lbl": f"{a['qre_lbl']}@{a_v}@{b['qre_lbl']}@{b_v}",
                                    "query": f"{qa} & {qb}"
                                }
                            })

                        lst_group_header.append(dict_grp_hd)
                        continue

                    for b_k, b_v in b['cats'].items():
                        # qb = f"{b['qre_name']} > 0" if str(b_k).upper() == 'TOTAL' else f"{b['qre_name']} == {b_k}"
                        qb = group_sig_table_header_query(b, b_k)

                        for c in lvl3:

                            if not c['cats']:
                                c['cats'] = get_cats_by_qre_name(c['qre_name'])

                            if not lvl4:
                                dict_grp_hd = dict()
                                dict_idx = {list(c['cats'].keys())[i]: i for i in range(len(c['cats'].keys()))}

                                for c_k, c_v in c['cats'].items():
                                    # qc = f"{c['qre_name']} > 0" if str(c_k).upper() == 'TOTAL' else f"{c['qre_name']} == {c_k}"
                                    qc = group_sig_table_header_query(c, c_k)

                                    dict_grp_hd.update({
                                        dict_idx[c_k]: {
                                            "lbl": f"{a['qre_lbl']}@{a_v}@{b['qre_lbl']}@{b_v}@{c['qre_lbl']}@{c_v}",
                                            "query": f"{qa} & {qb} & {qc}"
                                        }
                                    })

                                lst_group_header.append(dict_grp_hd)
                                continue

                            for c_k, c_v in c['cats'].items():
                                # qc = f"{c['qre_name']} > 0" if str(c_k).upper() == 'TOTAL' else f"{c['qre_name']} == {c_k}"
                                qc = group_sig_table_header_query(c, c_k)

                                for d in lvl4:

                                    if not d['cats']:
                                        d['cats'] = get_cats_by_qre_name(d['qre_name'])

                                    if not lvl5:
                                        dict_grp_hd = dict()
                                        dict_idx = {list(d['cats'].keys())[i]: i for i in range(len(d['cats'].keys()))}

                                        for d_k, d_v in d['cats'].items():
                                            # qd = f"{d['qre_name']} > 0" if str(d_k).upper() == 'TOTAL' else f"{d['qre_name']} == {d_k}"
                                            qd = group_sig_table_header_query(d, d_k)

                                            dict_grp_hd.update({
                                                dict_idx[d_k]: {
                                                    "lbl": f"{a['qre_lbl']}@{a_v}@{b['qre_lbl']}@{b_v}@{c['qre_lbl']}@{c_v}@{d['qre_lbl']}@{d_v}",
                                                    "query": f"{qa} & {qb} & {qc} & {qd}"
                                                }
                                            })

                                        lst_group_header.append(dict_grp_hd)
                                        continue

                                    for d_k, d_v in d['cats'].items():
                                        # qd = f"{d['qre_name']} > 0" if str(d_k).upper() == 'TOTAL' else f"{d['qre_name']} == {d_k}"
                                        qd = group_sig_table_header_query(d, d_k)

                                        for e in lvl5:

                                            if not e['cats']:
                                                e['cats'] = get_cats_by_qre_name(e['qre_name'])

                                            dict_grp_hd = dict()
                                            dict_idx = {list(e['cats'].keys())[i]: i for i in range(len(e['cats'].keys()))}

                                            for e_k, e_v in e['cats'].items():
                                                # qe = f"{e['qre_name']} > 0" if str(e_k).upper() == 'TOTAL' else f"{e['qre_name']} == {e_k}"
                                                qe = group_sig_table_header_query(e, e_k)

                                                dict_grp_hd.update({
                                                    dict_idx[e_k]: {
                                                        "lbl": f"{a['qre_lbl']}@{a_v}@{b['qre_lbl']}@{b_v}@{c['qre_lbl']}@{c_v}@{d['qre_lbl']}@{d_v}@{e['qre_lbl']}@{e_v}",
                                                        "query": f"{qa} & {qb} & {qc} & {qd} & {qe}"
                                                    }
                                                })

                                            lst_group_header.append(dict_grp_hd)

        return lst_group_header



    def run_standard_table_sig(self, tbl: dict) -> list:

        pd.set_option('future.no_silent_downcasting', True)

        df_tbl = pd.DataFrame()

        # create df_data with tbl_filter in json file
        df_data = self.df_data.query(tbl['tbl_filter']).copy() if tbl.get('tbl_filter') else self.df_data.copy()

        # create df_info with lst_side_qres in json file
        df_info = pd.DataFrame(columns=['var_name', 'var_lbl', 'var_type', 'val_lbl', 'val_lbl_unnetted', 'qre_fil'], data=[])

        for idx, qre in enumerate(tbl['lst_side_qres']):

            if '$' in qre['qre_name']:

                if '_RANK' in str(qre['qre_name']).upper():
                    # lst_qre_col = self.df_info.loc[self.df_info['var_name'].str.contains(f"^{qre['qre_name'][1:]}[0-9]+$"), 'var_name'].values.tolist()
                    lst_qre_col = self.df_info.loc[self.df_info['var_name'].str.contains(f"^{qre['qre_name'][1:]}_[0-9]+$"), 'var_name'].values.tolist()
                else:
                    lst_qre_col = self.df_info.loc[self.df_info['var_name'].str.contains(f"^{qre['qre_name'][1:]}_[0-9]+$"), 'var_name'].values.tolist()

                var_name = qre['qre_name'].replace('$', '')

            elif '#combine' in qre['qre_name']:
                var_name, str_comb = qre['qre_name'].split('#combine')
                lst_qre_col = str_comb.replace('(', '').replace(')', '').split(',')
            else:
                lst_qre_col = [qre['qre_name']]
                var_name = qre['qre_name']

            # NEW-------------------------------------------------------------------------------------------------------
            df_qre_info = self.df_info.query(f"var_name.isin({lst_qre_col})").copy()
            df_qre_info = df_qre_info.reset_index(drop=True)

            if df_qre_info.empty:
                self.print(f"\n\tQuestion(s) is not found: {qre['qre_name']}\n\tProcess terminated.", self.clr_err)
                exit()

            dict_row = {
                'var_index': int(idx),
                'var_name': var_name,
                'var_lbl': qre['qre_lbl'].replace('{lbl}', df_qre_info.at[0, 'var_lbl']) if qre.get('qre_lbl') else df_qre_info.at[0, 'var_lbl'],
                'var_type': 'MA_comb' if '#combine' in qre['qre_name'] else ('MA_Rank' if '$' in qre['qre_name'] and '_RANK' in str(qre['qre_name']).upper() else df_qre_info.at[0, 'var_type']),
                'val_lbl': qre['cats'] if qre.get('cats') else df_qre_info.at[0, 'val_lbl'],
                'val_lbl_unnetted': df_qre_info.at[0, 'val_lbl_unnetted'],
                'qre_fil': qre['qre_filter'] if qre.get('qre_filter') else "",
                'lst_qre_col': lst_qre_col,
                'mean': qre['mean'] if qre.get('mean') else {},
                'sort': qre['sort'] if qre.get('sort') else "",
                'calculate': qre['calculate'] if qre.get('calculate') else {},
                'friedman': qre['friedman'] if qre.get('friedman') else {},
                'weight_var': tbl['weight_var'] if tbl.get('weight_var') else "",
                'decimal': int(tbl['decimal']) if tbl.get('decimal') else 0,
            }

            df_info = pd.concat([df_info, pd.DataFrame(columns=list(dict_row.keys()), data=[list(dict_row.values())])], axis=0, ignore_index=True)
            df_info = df_info.set_index('var_index', drop=False)
            # ----------------------------------------------------------------------------------------------------------


        if tbl.get('lst_header_qres'):

            # PENDING
            # df_group_header = self.convert_table_header_to_dataframe(0, tbl['lst_header_qres'])  # test

            # Maximum 5 levels of header
            lst_group_header = self.convert_table_header_to_list(tbl['lst_header_qres'])

        else:
            # TO DO: Run multiple header with same level
            lst_group_header = list()

            df_group_header = pd.DataFrame()  # test

            lvl_hd = -1
            for int_header_group, (key_hd, val_hd) in enumerate(tbl['dict_header_qres'].items()):

                if lvl_hd == -1:
                    lvl_hd = len(val_hd)
                else:
                    if lvl_hd != len(val_hd):
                        self.print(f"Header don't have the same level: {tbl['dict_header_qres']}", self.clr_err)
                        exit()

                # PENDING
                # df_group_header = pd.concat([df_group_header, self.convert_table_header_to_dataframe(int_header_group, val_hd)], axis='rows')  # test

                # Maximum 5 levels for each header
                lst_group_header.extend(self.convert_table_header_to_list(val_hd))

        
        for grp_hd in lst_group_header:

            tbl_info_sig = {
                'tbl_name': tbl['tbl_name'],
                'is_count': tbl['is_count'],
                'is_pct_sign': tbl['is_pct_sign'],
                'decimal': int(tbl['decimal']) if tbl.get('decimal') else 0,
                'sig_test_info': tbl['sig_test_info'],
                'dict_grp_header': grp_hd,
                'weight_var': tbl.get('weight_var') if tbl.get('weight_var') else ''
            }

            df_temp = self.run_standard_header_sig(df_data, df_info, tbl_info_sig=tbl_info_sig)

            if df_tbl.empty:
                df_tbl = df_temp
            else:
                lst_col_temp_to_add = list(df_temp.columns)[6:]
                df_tbl = pd.concat([df_tbl, df_temp[lst_col_temp_to_add]], axis=1)


        # drop row which have all value is nan
        df_tbl = df_tbl.dropna(how='all')

        # Drop rows in qre oe that have all columns are 0
        if tbl['is_hide_oe_zero_cats']:

            df_sum_oe_val = df_tbl.query("qre_name.str.contains('_OE') & qre_type == 'MA'").copy()

            if not df_sum_oe_val.empty:
                fil_col = list(df_sum_oe_val.columns)
                df_sum_oe_val = df_sum_oe_val.loc[:, fil_col[5:]]
                df_sum_oe_val = df_sum_oe_val.replace({'': np.nan, 0: np.nan})

                # df_sum_oe_val = df_sum_oe_val.astype(float)
                # df_sum_oe_val['sum_val'] = df_sum_oe_val.sum(axis=1, skipna=True, numeric_only=True)

                df_sum_oe_val['sum_val'] = df_sum_oe_val.count(axis=1, numeric_only=True)

                df_sum_oe_val = df_sum_oe_val.query('sum_val == 0')

                df_tbl = df_tbl.drop(df_sum_oe_val.index)


        # # Drop columns which all value equal 0
        # if tbl['is_hide_zero_cols']:
        #
        #     start_idx = df_tbl.query(f"cat_val == 'base'").index.tolist()[0]
        #     lst_val_col = [v for i, v in enumerate(df_tbl.columns.tolist()[5:]) if i % 2 == 0]
        #
        #     df_fil = df_tbl.query("index >= @start_idx")[lst_val_col].copy()
        #     df_fil = df_fil.replace({0: np.nan}).dropna(axis='columns', how='all')
        #
        #     lst_keep_col = list()
        #     for i in df_fil.columns.tolist():
        #         lst_keep_col.extend([i, i.replace('@val@', '@sig@')])
        #
        #     df_tbl = df_tbl[df_tbl.columns.tolist()[:5] + lst_keep_col]
        #
        #     # df_tbl.to_excel('df_tbl_review.xlsx')


        return [tbl['tbl_name'], df_tbl]




    @staticmethod
    def add_base_to_tbl_sig(df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict, lst_sig_pair: list, weight_var: str = '') -> pd.DataFrame:

        lst_tbl_row_data = list()
        lst_ignore_col = list()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            for idx_item, item in enumerate(sig_pair):

                if item in lst_ignore_col:
                    continue

                df_filter = dict_header_col_name[item]['df_data'].copy()

                if len(weight_var) > 0:
                    lst_qre_col = qre_info['lst_qre_col']
                    df_fil_base = df_filter[lst_qre_col].dropna(how='all')
                else:
                    df_fil_base = df_filter.dropna(how='all')

                df_filter = df_filter.loc[df_fil_base.index, :]

                if df_filter.empty:
                    num_base = 0
                else:
                    num_base = df_filter.shape[0]

                if len(weight_var) > 0:
                    mean_weight = df_filter.loc[:, weight_var].mean()
                    num_base *= mean_weight

                if len(lst_tbl_row_data) == 0:
                    str_qre_name = qre_info['qre_name']
                    str_lbl = 'Weighted Base' if len(weight_var) > 0 else 'Base'
                    lst_tbl_row_data = [qre_info['qre_index'], str_qre_name, qre_info['qre_lbl'], qre_info['qre_type'], 'base', str_lbl, num_base, np.nan]
                else:
                    lst_tbl_row_data.extend([num_base, np.nan])

                lst_ignore_col.append(item)

        df_qre.loc[len(df_qre)] = lst_tbl_row_data
        return df_qre



    def add_sa_qre_val_to_tbl_sig(self, df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict,
                                  lst_sig_pair: list, sig_type: str, lst_sig_lvl: list,
                                  cat: str, lbl: str, lst_sub_cat: list | None, weight_var: str = '') -> pd.DataFrame:

        qre_index = qre_info['qre_index']
        qre_name = qre_info['qre_name']
        qre_lbl = qre_info['qre_lbl']
        qre_type = qre_info['qre_type']
        qre_val = qre_info['qre_val_unnetted']
        is_count = qre_info['is_count']
        val_pct = qre_info['val_pct']

        dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
        dict_new_row.update({
            'qre_index': qre_index,
            'qre_name': qre_name,
            'qre_lbl': qre_lbl,
            'qre_type': qre_type,
            'cat_val': cat,
            'cat_lbl': lbl,
        })

        df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

        lst_ran_col = list()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            dict_pair_to_sig = dict()

            for idx_item, item in enumerate(sig_pair):

                if not sig_type and item in lst_ran_col:
                    continue

                if item not in lst_ran_col:
                    lst_ran_col.append(item)

                # df_filter = dict_header_col_name[item]['df_data'].loc[:, [qre_name]].copy()
                df_filter = dict_header_col_name[item]['df_data'].copy()

                # # HERE: OPTIMIZING
                # df_des = df_filter.describe()
                # df_count = df_filter.value_counts()
                # df_pct = df_filter.value_counts(normalize=True)

                if df_filter.empty:
                    continue

                if lst_sub_cat:
                    dict_re_qre_val = {int(k): 1 if k in lst_sub_cat else 0 for k, v in qre_val.items()}
                else:
                    dict_re_qre_val = {int(k): 1 if k == cat else 0 for k, v in qre_val.items()}

                df_filter = df_filter.replace(dict_re_qre_val)

                dict_pair_to_sig.update({item: df_filter})

                # UPDATE FOR WEIGHTED TABLE
                if len(weight_var) > 0:

                    df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{qre_name}.isnull()"), qre_name].copy()

                    if df_temp_for_weight.empty:
                        num_val = np.nan
                    else:
                        if is_count:
                            num_val = np.dot(df_temp_for_weight, dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var])
                        else:
                            num_val = np.average(df_temp_for_weight, weights=dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var]) * val_pct

                else:
                    num_val = (df_filter[qre_name] == 1).sum() if is_count else df_filter[qre_name].mean() * val_pct

                val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                if sig_type and lst_sig_lvl:
                    num_val_old = df_qre.loc[df_qre['cat_val'] == cat, [val_col_name]].values[0, 0]

                    if pd.isnull(num_val_old):
                        df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]

                else:

                    df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]




            if sig_type and lst_sig_lvl and len(weight_var) == 0:
                df_qre = self.mark_sig_to_df_qre(df_qre, dict_pair_to_sig, sig_pair, dict_header_col_name, sig_type, lst_sig_lvl)




        return df_qre



    def add_sa_qre_mean_to_tbl_sig(self, df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict,
                                   lst_sig_pair: list, sig_type: str, lst_sig_lvl: list, mean_factor: dict,
                                   is_mean: bool, weight_var: str = '', is_friedman_sig: bool = False, is_sem: bool = False) -> pd.DataFrame:

        qre_index = qre_info['qre_index']
        qre_name = qre_info['qre_name']
        qre_lbl = qre_info['qre_lbl']
        qre_type = qre_info['qre_type']
        # qre_val = qre_info['qre_val']
        qre_val = qre_info['qre_val_unnetted']

        if is_mean:
            dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
            dict_new_row.update({
                'qre_index': qre_index,
                'qre_name': qre_name,
                'qre_lbl': qre_lbl,
                'qre_type': qre_type,
                'cat_val': 'mean',
                'cat_lbl': 'Mean',
            })

        elif is_friedman_sig:

            dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
            dict_new_row.update({
                'qre_index': qre_index,
                'qre_name': qre_name,
                'qre_lbl': qre_lbl,
                'qre_type': qre_type,
                'cat_val': 'friedman_pval',
                'cat_lbl': 'Friedman P-value',
            })

        elif is_sem:

            dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
            dict_new_row.update({
                'qre_index': qre_index,
                'qre_name': qre_name.replace('_Mean', '_Sem'),
                'qre_lbl': qre_lbl,
                'qre_type': qre_type,
                'cat_val': 'sem',
                'cat_lbl': 'Standard Error',
            })

        else:

            dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
            dict_new_row.update({
                'qre_index': qre_index,
                'qre_name': qre_name.replace('_Mean', '_Std'),
                'qre_lbl': qre_lbl,
                'qre_type': qre_type,
                'cat_val': 'std',
                'cat_lbl': 'Std',
            })

        org_qre_name = qre_name.replace('_Mean', '')

        df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

        lst_ran_col = list()

        dict_sig_friedman = dict()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            dict_pair_to_sig = dict()

            for idx_item, item in enumerate(sig_pair):

                if not sig_type and item in lst_ran_col:
                    continue

                if item not in lst_ran_col:
                    lst_ran_col.append(item)

                # df_filter = dict_header_col_name[item]['df_data'].loc[:, [org_qre_name]].copy()
                df_filter = dict_header_col_name[item]['df_data'].copy()


                if df_filter.empty:
                    continue

                if mean_factor:
                    df_filter = df_filter.replace({org_qre_name: mean_factor})

                if -999 not in qre_val.keys():

                    try:

                        df_filter = df_filter.replace(qre_val)

                    except TypeError as err:
                        raise err


                dict_pair_to_sig.update({item: df_filter})

                if is_friedman_sig:
                    if item in dict_sig_friedman.keys():
                        continue

                    dict_sig_friedman.update({item: df_filter})

                if is_mean:

                    # UPDATE FOR WEIGHTED TABLE
                    if len(weight_var) > 0:

                        df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{org_qre_name}.isnull()"), org_qre_name].copy()

                        if df_temp_for_weight.empty:
                            num_val = np.nan
                        else:
                            num_val = np.average(df_temp_for_weight, weights=dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var])
                    else:
                        num_val = df_filter[org_qre_name].mean()


                    val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                    if sig_type and lst_sig_lvl:

                        num_val_old = df_qre.loc[df_qre['cat_val'] == 'mean', [val_col_name]].values[0, 0]

                        if pd.isnull(num_val_old):
                            df_qre.loc[df_qre['cat_val'] == 'mean', [val_col_name, sig_col_name]] = [num_val, np.nan]

                    else:
                        df_qre.loc[df_qre['cat_val'] == 'mean', [val_col_name, sig_col_name]] = [num_val, np.nan]



                    pd.DataFrame()

                elif is_sem:

                    # UPDATE FOR WEIGHTED TABLE
                    if len(weight_var) > 0:

                        df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{org_qre_name}.isnull()"), org_qre_name].copy()

                        if df_temp_for_weight.empty:
                            num_val_sem = np.nan
                        else:
                            df_weight = dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var].copy()
                            num_mean = np.average(df_temp_for_weight, weights=df_weight)
                            num_variance = np.average((df_temp_for_weight - num_mean) ** 2, weights=df_weight)
                            num_val_sem = math.sqrt(num_variance) / math.sqrt(sum(df_weight))

                    else:
                        num_val_sem = df_filter[org_qre_name].sem()

                    val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                    df_qre.loc[df_qre['cat_val'] == 'sem', [val_col_name, sig_col_name]] = [num_val_sem, np.nan]


                else:

                    # UPDATE FOR WEIGHTED TABLE
                    if len(weight_var) > 0:

                        df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{org_qre_name}.isnull()"), org_qre_name].copy()

                        if df_temp_for_weight.empty:
                            num_val_std = np.nan
                        else:
                            df_weight = dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var].copy()
                            num_mean = np.average(df_temp_for_weight, weights=df_weight)
                            num_variance = np.average((df_temp_for_weight - num_mean) ** 2, weights=df_weight)
                            num_val_std = math.sqrt(num_variance)
                    else:
                        num_val_std = df_filter[org_qre_name].std()

                    val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                    df_qre.loc[df_qre['cat_val'] == 'std', [val_col_name, sig_col_name]] = [num_val_std, np.nan]


            if len(weight_var) > 0 or (not is_mean and not is_friedman_sig):
                continue

            if is_mean:
                if sig_type and lst_sig_lvl:
                    df_qre = self.mark_sig_to_df_qre(df_qre, dict_pair_to_sig, sig_pair, dict_header_col_name, sig_type, lst_sig_lvl)


        if is_friedman_sig:

            lst_val_col_name = list()
            for k in dict_sig_friedman.keys():
                lst_val_col_name.append(dict_header_col_name[k]['val_col'])

            if len(dict_sig_friedman.keys()) < 3:
                df_qre.loc[df_qre['cat_val'] == 'friedman_pval', lst_val_col_name] = ['NAN'] * len(lst_val_col_name)

            else:
                df_friedman_sig = pd.DataFrame()

                for k, df in dict_sig_friedman.items():
                    df_frm_temp = df.reset_index(drop=True)
                    df_friedman_sig = pd.concat([df_friedman_sig, df_frm_temp], axis=1, ignore_index=True)

                arr_friedman_sig = df_friedman_sig.to_numpy()
                arr_friedman_sig = arr_friedman_sig.transpose()
                frm = stats.friedmanchisquare(*arr_friedman_sig)

                df_qre.loc[df_qre['cat_val'] == 'friedman_pval', lst_val_col_name] = [frm.pvalue] * len(lst_val_col_name)


        return df_qre



    def add_sa_qre_group_to_tbl_sig(self, df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict,
                                    lst_sig_pair: list, sig_type: str, lst_sig_lvl: list, cat: str, lbl: str,
                                    weight_var: str = '') -> pd.DataFrame:


        qre_name = qre_info['qre_name']
        qre_lbl = qre_info['qre_lbl']
        qre_type = qre_info['qre_type']
        qre_val = qre_info['qre_val']
        is_count = qre_info['is_count']
        val_pct = qre_info['val_pct']

        dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
        dict_new_row.update({
            'qre_name': qre_name,
            'qre_lbl': qre_lbl,
            'qre_type': qre_type,
            'cat_val': cat,
            'cat_lbl': lbl,
        })

        org_qre_name = qre_name.replace('_Group', '')

        df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

        lst_ran_col = list()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            dict_pair_to_sig = dict()

            for idx_item, item in enumerate(sig_pair):

                if not sig_type and item in lst_ran_col:
                    continue

                if item not in lst_ran_col:
                    lst_ran_col.append(item)

                df_filter = dict_header_col_name[item]['df_data'].loc[:, [org_qre_name]].copy()

                if df_filter.empty:
                    continue

                df_filter = df_filter.replace(qre_val['recode'])

                dict_re_qre_val = {int(k): 1 if int(k) == int(cat) else 0 for k, v in qre_val['cats'].items()}
                df_filter = df_filter.replace(dict_re_qre_val)

                dict_pair_to_sig.update({item: df_filter})

                # UPDATE FOR WEIGHTED TABLE
                if len(weight_var) > 0:

                    df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{org_qre_name}.isnull()"), org_qre_name].copy()

                    if df_temp_for_weight.empty:
                        num_val = np.nan
                    else:
                        if is_count:
                            num_val = np.dot(df_temp_for_weight, dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var])
                        else:
                            num_val = np.average(df_temp_for_weight, weights=dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var]) * val_pct

                else:
                    num_val = (df_filter[org_qre_name] == 1).sum() if is_count else df_filter[org_qre_name].mean() * val_pct

                val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                if sig_type and lst_sig_lvl:

                    num_val_old = df_qre.loc[df_qre['cat_val'] == cat, [val_col_name]].values[0, 0]

                    if pd.isnull(num_val_old):
                        df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]

                else:

                    df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]


            if sig_type and lst_sig_lvl and len(weight_var) == 0:
                df_qre = self.mark_sig_to_df_qre(df_qre, dict_pair_to_sig, sig_pair, dict_header_col_name, sig_type, lst_sig_lvl)

        return df_qre



    @staticmethod
    def add_sa_qre_cal_to_tbl_sig(df_qre: pd.DataFrame, qre_info: dict, dict_cal: dict) -> pd.DataFrame:

        df_qre['idx_by_cat_lbl'] = df_qre['cat_lbl']
        df_qre = df_qre.set_index('idx_by_cat_lbl')

        for key, val in dict_cal.items():

            dict_new_row = {col: '' if '@sig@' in col else dict_cal.get('syntax') for col in df_qre.columns}
            dict_new_row.update({
                'qre_index': qre_info['qre_index'],
                'qre_name': qre_info['qre_name'],
                'qre_lbl': qre_info['qre_lbl'],
                'qre_type': qre_info['qre_type'],
                'cat_val': f'calculate|{key}',
                'cat_lbl': key,
            })

            df_temp = pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])

            # df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

            df_temp['idx_by_cat_lbl'] = df_temp['cat_lbl']
            df_temp = df_temp.set_index('idx_by_cat_lbl')

            for col in df_temp.columns:
                if '@val@' not in col:
                    continue

                str_syntax = val.replace('[', f"df_qre.loc['").replace(']', f"', '{col}']")

                df_temp.loc[key, col] = eval(str_syntax)

            # HERE: Find solution for warning
            # a = 0

            df_qre = pd.concat([df_qre, df_temp], axis=0)

            # a = 1


        df_qre = df_qre.reset_index(drop=True)

        return df_qre



    def add_num_qre_to_tbl_sig(self, df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict, cal_act: str,
                               lst_sig_pair: list, sig_type: str, lst_sig_lvl: list, weight_var: str = '') -> pd.DataFrame:

        # Add option: std, quantile 25/50/75, min, max, sem
        dict_cal_act = {
            'mean': 'Mean',
            'std': 'Std',
            'sem': 'Standard Error',
            'min': 'Minimum',
            'max': 'Maximum',
            '25%': 'Quantile 25%',
            '50%': 'Quantile 50%',
            '75%': 'Quantile 75%',
        }

        qre_index = qre_info['qre_index']
        qre_name = qre_info['qre_name']
        qre_lbl = qre_info['qre_lbl']
        qre_type = qre_info['qre_type']

        dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
        dict_new_row.update({
            'qre_index': qre_index,
            'qre_name': qre_name,
            'qre_lbl': qre_lbl,
            'qre_type': qre_type,
            'cat_val': cal_act,
            'cat_lbl': dict_cal_act.get(cal_act),
        })

        df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

        lst_ran_col = list()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            dict_pair_to_sig = dict()

            for idx_item, item in enumerate(sig_pair):

                if not sig_type and item in lst_ran_col:
                    continue

                if item not in lst_ran_col:
                    lst_ran_col.append(item)

                # df_filter = dict_header_col_name[item]['df_data'].loc[:, [qre_name]].copy()
                df_filter = dict_header_col_name[item]['df_data'].copy()

                if df_filter.empty:
                    continue

                dict_pair_to_sig.update({item: df_filter})

                # UPDATE FOR WEIGHTED TABLE
                if len(weight_var) > 0:

                    df_temp_for_weight = df_filter.loc[df_filter.eval(f"~{qre_name}.isnull()"), qre_name].copy()

                    if df_temp_for_weight.empty:
                        num_val = np.nan
                    else:
                        df_weight = dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var].copy()

                        if cal_act in ['std']:
                            num_mean = np.average(df_temp_for_weight, weights=df_weight)
                            num_variance = np.average((df_temp_for_weight - num_mean) ** 2, weights=df_weight)
                            num_val = math.sqrt(num_variance)

                        elif cal_act in ['sem']:
                            num_mean = np.average(df_temp_for_weight, weights=df_weight)
                            num_variance = np.average((df_temp_for_weight - num_mean) ** 2, weights=df_weight)
                            num_val = math.sqrt(num_variance) / math.sqrt(sum(df_weight))

                        elif cal_act in ['min', 'max']:
                            num_val = df_filter[qre_name].describe().loc[cal_act]

                        elif cal_act in ['25%', '50%', '75%']:

                            def weighted_percentile(data, percents, weights=None):
                                """ percents in units of 1%
                                weights specifies the frequency (count) of data.
                                """
                                if weights is None:
                                    return np.percentile(data, percents)
                                ind = np.argsort(data)
                                d = data[ind]
                                w = weights[ind]
                                p = 1. * w.cumsum() / w.sum() * 100
                                y = np.interp(percents, p, d)
                                return y

                            num_val = weighted_percentile(np.array(df_temp_for_weight), int(cal_act.replace('%', '')), np.array(df_weight))

                        else:
                            num_val = np.average(df_temp_for_weight, weights=dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var])

                else:

                    if cal_act == 'sem':
                        num_val = df_filter[qre_name].sem()

                    else:
                        num_val = df_filter[qre_name].describe().loc[cal_act]




                val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                if sig_type and lst_sig_lvl:

                    num_val_old = df_qre.loc[df_qre['cat_val'] == cal_act, [val_col_name]].values[0, 0]

                    if pd.isnull(num_val_old):
                        df_qre.loc[df_qre['cat_val'] == cal_act, [val_col_name, sig_col_name]] = [num_val, np.nan]

                else:
                    df_qre.loc[df_qre['cat_val'] == cal_act, [val_col_name, sig_col_name]] = [num_val, np.nan]

            if sig_type and lst_sig_lvl and len(weight_var) == 0 and cal_act == 'mean':
                df_qre = self.mark_sig_to_df_qre(df_qre, dict_pair_to_sig, sig_pair, dict_header_col_name, sig_type, lst_sig_lvl)

        return df_qre



    def add_ma_qre_val_to_tbl_sig(self, df_qre: pd.DataFrame, qre_info: dict, dict_header_col_name: dict,
                                  lst_sig_pair: list, sig_type: str, lst_sig_lvl: list, cat: str, lbl: str,
                                  lst_sub_cat: list | None, weight_var: str = '') -> pd.DataFrame:

        if lst_sub_cat is None:
            lst_sub_cat = []

        qre_index = qre_info['qre_index']
        qre_name = qre_info['qre_name']
        qre_lbl = qre_info['qre_lbl']
        qre_type = qre_info['qre_type']
        qre_val = qre_info['qre_val_unnetted']
        is_count = qre_info['is_count']
        val_pct = qre_info['val_pct']
        # df_ma_info = qre_info['df_ma_info']
        lst_qre_col = qre_info['lst_qre_col']

        dict_new_row = {col: '' if '@sig@' in col else np.nan for col in df_qre.columns}
        dict_new_row.update({
            'qre_index': qre_index,
            'qre_name': qre_name,  # qre_name.rsplit('_', 1)[0],
            'qre_lbl': qre_lbl,
            'qre_type': qre_type,
            'cat_val': cat,
            'cat_lbl': lbl,
        })

        df_qre = pd.concat([df_qre, pd.DataFrame(columns=list(dict_new_row.keys()), data=[list(dict_new_row.values())])], axis=0, ignore_index=True)

        lst_ran_col = list()

        for idx_pair, sig_pair in enumerate(lst_sig_pair):

            dict_pair_to_sig = dict()

            for idx_item, item in enumerate(sig_pair):

                if not sig_type and item in lst_ran_col:
                    continue

                if item not in lst_ran_col:
                    lst_ran_col.append(item)

                # df_filter = dict_header_col_name[item]['df_data'].loc[:, lst_qre_col].copy()
                df_filter = dict_header_col_name[item]['df_data'].copy()


                if df_filter.empty:
                    continue

                if lst_sub_cat:
                    dict_re_qre_val = {int(k): 1 if k in lst_sub_cat else 0 for k, v in qre_val.items()}

                else:
                    dict_re_qre_val = {int(k): 1 if k == cat else 0 for k, v in qre_val.items()}

                df_filter = df_filter.replace(dict_re_qre_val)

                if len(weight_var) > 0:
                    df_fil_base = df_filter[lst_qre_col].dropna(how='all')

                else:
                    df_fil_base = df_filter.dropna(how='all')

                df_filter.loc[df_fil_base.index, 'ma_val_sum'] = df_filter.loc[df_fil_base.index, lst_qre_col].sum(axis='columns')

                if lst_sub_cat or qre_type == 'MA_comb':
                    df_filter.loc[df_filter['ma_val_sum'] > 1, 'ma_val_sum'] = 1

                dict_pair_to_sig.update({item: df_filter['ma_val_sum']})

                # UPDATE FOR WEIGHTED TABLE
                if len(weight_var) > 0:

                    df_temp_for_weight = df_filter.loc[df_filter.eval(f"~ma_val_sum.isnull()"), 'ma_val_sum'].copy()

                    if df_temp_for_weight.empty:
                        num_val = np.nan
                    else:

                        if is_count:
                            num_val = np.dot(df_temp_for_weight, dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var])
                        else:
                            num_val = np.average(df_temp_for_weight, weights=dict_header_col_name[item]['df_data'].loc[df_temp_for_weight.index, weight_var]) * val_pct

                else:
                    num_val = (df_filter['ma_val_sum'] == 1).sum() if is_count else df_filter['ma_val_sum'].mean() * val_pct



                val_col_name, sig_col_name = dict_header_col_name[item]['val_col'], dict_header_col_name[item]['sig_col']

                if sig_type and lst_sig_lvl:
                    num_val_old = df_qre.loc[df_qre['cat_val'] == cat, [val_col_name]].values[0, 0]

                    if pd.isnull(num_val_old):
                        df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]

                else:
                    df_qre.loc[df_qre['cat_val'] == cat, [val_col_name, sig_col_name]] = [num_val, np.nan]

            if sig_type and lst_sig_lvl and len(weight_var) == 0:
                df_qre = self.mark_sig_to_df_qre(df_qre, dict_pair_to_sig, sig_pair, dict_header_col_name, sig_type, lst_sig_lvl)

        return df_qre




    def mark_sig_to_df_qre(self, df_qre: pd.DataFrame, dict_pair_to_sig: dict, sig_pair: list, dict_header_col_name: dict, sig_type: str, lst_sig_lvl: list) -> pd.DataFrame:

        if not lst_sig_lvl or not sig_type or not dict_pair_to_sig:
            return df_qre

        if sig_type not in ['rel', 'ind']:
            self.print(f"\nSig type must be 'rel' or 'ind' instead of '{sig_type}'", self.clr_err)
            raise ValueError(sig_type)

        if sig_pair[0] not in dict_pair_to_sig.keys() or sig_pair[1] not in dict_pair_to_sig.keys():
            return df_qre

        df_left, df_right = dict_pair_to_sig[sig_pair[0]], dict_pair_to_sig[sig_pair[1]]

        df_left = df_left.dropna()
        df_right = df_right.dropna()

        if df_left.shape[0] < 30 or df_right.shape[0] < 30:
            return df_qre

        is_df_left_null = df_left.isnull().values.all()
        is_df_right_null = df_right.isnull().values.all()

        if is_df_left_null or is_df_right_null:
            return df_qre

        try:
            if df_left.mean().iloc[0] == 0 or df_right.mean().iloc[0] == 0:
                return df_qre

            if df_left.mean().iloc[0] == 1 and df_right.mean().iloc[0] == 1:
                return df_qre

        except Exception as ex:

            if df_left.mean() == 0 or df_right.mean() == 0:
                return df_qre

            if df_left.mean() == 1 and df_right.mean() == 1:
                return df_qre

        arr_left = df_left.to_numpy(dtype=float).flatten()
        arr_right = df_right.to_numpy(dtype=float).flatten()

        with warnings.catch_warnings():

            warnings.simplefilter("ignore", RuntimeWarning)

            match sig_type:
                case 'rel':

                    if df_left.shape[0] != df_right.shape[0]:
                        return df_qre

                    # sigResult = stats.ttest_rel(df_left, df_right)
                    sigResult = stats.ttest_rel(arr_left, arr_right)


                case 'ind':

                    # sigResult = stats.ttest_ind(df_left, df_right)
                    sigResult = stats.ttest_ind(arr_left, arr_right)

                case _:

                    raise ValueError(sig_type)



        if sigResult.pvalue:
            if sigResult.statistic > 0:
                mark_sig_char = sig_pair[1]
                sig_col_name = dict_header_col_name[sig_pair[0]]['sig_col']
            else:
                mark_sig_char = sig_pair[0]
                sig_col_name = dict_header_col_name[sig_pair[1]]['sig_col']

            if sigResult.pvalue <= lst_sig_lvl[0]:
                df_qre.at[df_qre.index[-1], sig_col_name] = str(df_qre.at[df_qre.index[-1], sig_col_name]).replace('nan', '') + mark_sig_char.upper()

            elif len(lst_sig_lvl) >= 2:

                if sigResult.pvalue <= lst_sig_lvl[1]:
                    df_qre.loc[df_qre.index[-1], sig_col_name] = str(df_qre.at[df_qre.index[-1], sig_col_name]).replace('nan', '') + mark_sig_char.lower()


        return df_qre



    def run_standard_header_sig(self, df_data: pd.DataFrame, df_info: pd.DataFrame, tbl_info_sig: dict) -> pd.DataFrame:

        is_count = tbl_info_sig['is_count']
        val_pct = 1 if tbl_info_sig['is_pct_sign'] else 100

        sig_type = tbl_info_sig['sig_test_info']['sig_type']

        lst_sig_lvl_pct = tbl_info_sig['sig_test_info']['lst_sig_lvl']
        lst_sig_lvl = [(100 - a) / 100 for a in lst_sig_lvl_pct]
        lst_sig_lvl.reverse()

        dict_grp_header = tbl_info_sig['dict_grp_header']

        dict_char_sig = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y'}

        # lst_tbl_col = ['qre_name', 'qre_lbl', 'qre_type', 'cat_val', 'cat_lbl']
        dict_tbl_data = {
            'qre_index': list(),
            'qre_name': list(),
            'qre_lbl': list(),
            'qre_type': list(),
            'cat_val': list(),
            'cat_lbl': list(),
        }

        dict_header_col_name_origin = dict()
        # df_data_query = pd.DataFrame()

        for hd_k, hd_v in dict_grp_header.items():
            str_hd_val = f"{hd_v['query']}@{hd_v['lbl']}@val@{dict_char_sig[hd_k]}"
            str_hd_sig = f"{hd_v['query']}@{hd_v['lbl']}@sig@{dict_char_sig[hd_k]}"

            dict_tbl_data.update({
                str_hd_val: str_hd_val.split('@'),
                str_hd_sig: str_hd_sig.split('@'),
            })

            try:
                df_data_query = df_data.query(hd_v['query']).copy()
            except ValueError:
                self.print(f"\tValueError, Cannot process: {hd_v}", self.clr_err)
                exit()
            except pd.errors.UndefinedVariableError:
                self.print(f"\tpandas.errors.UndefinedVariableError, Cannot process: {hd_v}", self.clr_err)
                exit()

            dict_header_col_name_origin.update({
                dict_char_sig[hd_k]: {
                    'val_col': str_hd_val,
                    'sig_col': str_hd_sig,
                    'df_data': df_data_query,
                }
            })

            if len(dict_tbl_data['qre_name']) == 0:
                arr_nan = [np.nan] * len(str_hd_val.split('@'))
                dict_tbl_data.update({
                    'qre_index': arr_nan,
                    'qre_name': arr_nan,
                    'qre_lbl': arr_nan,
                    'qre_type': arr_nan,
                    'cat_val': arr_nan,
                    'cat_lbl': arr_nan,
                })

        if sig_type in ["ind", "rel"]:

            if tbl_info_sig['sig_test_info']['sig_cols']:
                lst_sig_pair = tbl_info_sig['sig_test_info']['sig_cols']
            else:
                lst_sig_char = list(dict_header_col_name_origin.keys())
                lst_sig_pair = list()
                for i in range(len(lst_sig_char)-1):
                    for j in range(i + 1, len(lst_sig_char)):
                        lst_sig_pair.append([lst_sig_char[i], lst_sig_char[j]])

        else:
            lst_sig_char = list(dict_header_col_name_origin.keys())
            lst_sig_pair = list()

            for i in lst_sig_char:
                lst_sig_pair.append([i])


        df_tbl = pd.DataFrame.from_dict(dict_tbl_data)

        df_tbl['qre_lbl'] = df_tbl['qre_lbl'].astype('object')

        # lst_tbl_info = [f"Cell content: {'count' if is_count else ('percentage(%)' if tbl_info_sig['is_pct_sign'] else 'percentage')}"]

        str_decimal = f"0.{'0' * tbl_info_sig['decimal']}" if tbl_info_sig['decimal'] > 0 else '0'
        lst_tbl_info = [f"Cell content: {'count' if is_count else (f'percentage ({str_decimal}%)' if tbl_info_sig['is_pct_sign'] else f'percentage ({str_decimal})')}"]

        if not is_count and sig_type != '':
            lst_tbl_info.extend([
                f"{'Dependent' if sig_type == 'rel' else 'Independent'} Pair T-test at level {' & '.join([f'{i}%' for i in lst_sig_lvl_pct])}",
                f"Columns Tested: {', '.join(['/'.join(i) for i in lst_sig_pair])}",
                f"Uppercase for {lst_sig_lvl_pct[-1]}%, lowercase for {lst_sig_lvl_pct[0]}%" if len(lst_sig_lvl_pct) > 1 else np.nan
            ])

        if len(tbl_info_sig['weight_var']) > 0:
            lst_tbl_info.extend([f"Weighted with: {tbl_info_sig['weight_var']}"])

        df_tbl.loc[1:len(lst_tbl_info), ['qre_lbl']] = lst_tbl_info

        # lst_ft_qre_warn = list()

        for idx in df_info.index:

            qre_idx = int(df_info.at[idx, 'var_index'])
            qre_name = df_info.at[idx, 'var_name']
            qre_lbl = df_info.at[idx, 'var_lbl']
            qre_type = df_info.at[idx, 'var_type']
            qre_val = eval(df_info.at[idx, 'val_lbl']) if isinstance(df_info.at[idx, 'val_lbl'], str) else df_info.at[idx, 'val_lbl']
            qre_val_unnetted = df_info.at[qre_idx, 'val_lbl_unnetted']
            qre_fil = df_info.at[idx, 'qre_fil']
            lst_qre_col = df_info.at[idx, 'lst_qre_col']
            weight_var = df_info.at[idx, 'weight_var']
            lst_qre_col_weight_var = lst_qre_col if len(weight_var) == 0 else lst_qre_col + [weight_var]

            dict_header_col_name = dict()
            for key, val in dict_header_col_name_origin.items():
                dict_header_col_name[key] = val.copy()

                if len(qre_fil) > 0:
                    dict_header_col_name[key]['df_data'] = dict_header_col_name[key]['df_data'].query(qre_fil)

                dict_header_col_name[key]['df_data'] = dict_header_col_name[key]['df_data'][lst_qre_col_weight_var]

            qre_info = {
                'qre_index': qre_idx,
                'qre_name': qre_name,
                'qre_lbl': qre_lbl,
                'qre_type': qre_type,
                'qre_val': qre_val,
                'qre_val_unnetted': qre_val_unnetted,
                'is_count': is_count,
                'val_pct': val_pct,
                'lst_qre_col': lst_qre_col,
            }

            lst_grp_header_item = list()
            for v in dict_grp_header.values():
                lst_grp_header_item.extend(v['lbl'].rsplit('@', 1))

            lst_grp_header_item = list(dict.fromkeys(lst_grp_header_item))

            self.print(
                ['Populate table', tbl_info_sig['tbl_name'], f"{lst_grp_header_item[0]} - [{', '.join(lst_grp_header_item[1:])}]", f"{qre_name} - {qre_type}"],
                [None, self.clr_blue, self.clr_cyan_light, self.clr_magenta_light],
                sep=' | ', end='')





            df_qre = pd.DataFrame(columns=df_tbl.columns, data=[])

            # BASE------------------------------------------------------------------------------------------------------
            df_qre = self.add_base_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, weight_var)
            # END BASE--------------------------------------------------------------------------------------------------

            if qre_type in ['FT', 'FT_mtr']:
                # Not run free text questions
                # lst_ft_qre_warn.extend([f'{qre_name}|{qre_type}'])
                pass

            elif qre_type in ['NUM']:

                if not qre_info.get('qre_val'):
                    qre_info['qre_val'] = {
                        'mean': 'Mean',
                        'std': 'Std',
                        'sem': 'Standard Error',
                        'min': 'Minimum',
                        'max': 'Maximum',
                        '25%': 'Quantile 25%',
                        '50%': 'Quantile 50%',
                        '75%': 'Quantile 75%',
                    }

                for key_num_opt in qre_info['qre_val'].keys():
                    df_qre = self.add_num_qre_to_tbl_sig(df_qre, qre_info, dict_header_col_name, key_num_opt, lst_sig_pair, sig_type, lst_sig_lvl, weight_var)


            elif qre_type in ['SA', 'SA_mtr', 'RANKING']:

                # qre_info['qre_val'] = df_info.at[qre_name, 'val_lbl_unnetted']

                # HERE
                # NEED TO OPTIMIZE


                for cat, lbl in qre_val.items():

                    # ADD-IN Net Code
                    if 'net_code' in str(cat):

                        for net_cat, net_val in qre_val['net_code'].items():

                            if isinstance(net_val, dict):

                                lst_sub_cat = list(net_val.keys())

                                # "900001|combine|POSITIVE (NET)"
                                # list_net_cat = net_cat.split('|')
                                net_cat_val, net_cat_type, net_cat_lbl = net_cat.split('|')

                                df_qre = self.add_sa_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, net_cat_val, net_cat_lbl, lst_sub_cat, weight_var)

                                if 'NET' in net_cat_type.upper():
                                    for cat2, lbl2 in net_val.items():
                                        df_qre = self.add_sa_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, cat2, f' - {lbl2}', None, weight_var)

                                df_qre.loc[df_qre['cat_val'] == net_cat_val, 'cat_val'] = f'{net_cat_val}|{net_cat_type}'

                            else:
                                df_qre = self.add_sa_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, net_cat, net_val, None, weight_var)

                    else:
                        df_qre = self.add_sa_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, cat, lbl, None, weight_var)

                mean_factor = df_info.at[idx, 'mean']
                if mean_factor.keys():
                    # Run Mean
                    df_qre = self.add_sa_qre_mean_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, mean_factor, is_mean=True, weight_var=weight_var)

                    # Run Std
                    df_qre = self.add_sa_qre_mean_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, mean_factor, is_mean=False, weight_var=weight_var)

                    # Run Standard Error
                    df_qre = self.add_sa_qre_mean_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, mean_factor, is_mean=False, weight_var=weight_var, is_sem=True)

                friedman_factor = df_info.at[idx, 'friedman']
                if friedman_factor.keys():
                    df_qre = self.add_sa_qre_mean_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, mean_factor=friedman_factor, is_mean=False, weight_var=weight_var, is_friedman_sig=True)


                dict_cal = df_info.at[idx, 'calculate']
                if dict_cal:
                    df_qre = self.add_sa_qre_cal_to_tbl_sig(df_qre, qre_info, dict_cal)


            elif qre_type in ['MA', 'MA_mtr', 'MA_comb', 'MA_Rank']:

                # qre_info['qre_val'] = df_info.at[qre_name, 'val_lbl_unnetted']

                for cat, lbl in qre_val.items():

                    # ADD-IN Net Code
                    if 'net_code' in cat:

                        for net_cat, net_val in qre_val['net_code'].items():

                            if isinstance(net_val, dict):

                                lst_sub_cat = list(net_val.keys())

                                # "900001|combine|POSITIVE (NET)"
                                # list_net_cat = net_cat.split('|')
                                net_cat_val, net_cat_type, net_cat_lbl = net_cat.split('|')

                                df_qre = self.add_ma_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, net_cat_val, net_cat_lbl, lst_sub_cat, weight_var)

                                if 'NET' in net_cat_type.upper():
                                    for cat2, lbl2 in net_val.items():
                                        df_qre = self.add_ma_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, cat2, f' - {lbl2}', None, weight_var)

                                df_qre.loc[df_qre['cat_val'] == net_cat_val, 'cat_val'] = f'{net_cat_val}|{net_cat_type}'

                            else:
                                df_qre = self.add_ma_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, net_cat, net_val, None, weight_var)

                    else:
                        df_qre = self.add_ma_qre_val_to_tbl_sig(df_qre, qre_info, dict_header_col_name, lst_sig_pair, sig_type, lst_sig_lvl, cat, lbl, None, weight_var)




            # # BUGGING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # # SORTING---------------------------------------------------------------------------------------------------
            # sort_opt = df_info.at[idx, 'sort']
            #
            # # if sort_opt:
            # #     is_asc = True if sort_opt == 'asc' else False
            # #     base_val = -999_999_999 if sort_opt == 'asc' else 999_999_999
            # #
            # #     df_qre['sort_col'] = df_qre[df_qre.columns.tolist()[5]]
            # #     df_qre.loc[df_qre['cat_val'] == 'base', 'sort_col'] = base_val
            # #
            # #     df_qre.sort_values(by=['sort_col'], ascending=is_asc, inplace=True, ignore_index=True)
            # #     df_qre.drop(columns=['sort_col'], inplace=True)
            #
            # # END SORTING-----------------------------------------------------------------------------------------------


            df_tbl = pd.concat([df_tbl, df_qre], axis=0, ignore_index=True)

            print(end='\r')


        # self.print(f'Cannot create table for free text questions: {lst_ft_qre_warn}', self.clr_warn)

        return df_tbl



    # NEW---------------------------------------------------------------------------------------------------------------


    @staticmethod
    def convert_table_header_to_dataframe(*, header_group: int, lst_header_qres: list, df_info: pd.DataFrame) -> pd.DataFrame:

        def get_cats_by_qre_name(qre_name: str) -> dict:
            str_qre_name = f'{qre_name[1:]}_1' if '$' in qre_name else qre_name
            return df_info.loc[df_info.eval(f"var_name == '{str_qre_name}'"), 'val_lbl'].values[0]



        def get_header_query_by_cats(qre_name: str, qre_lbl: str, tpl_cat: tuple) -> list:

            # str_header_label = f"{qre_lbl}@{tpl_cat[1]}"

            if '$' in qre_name:

                if 'RANK' in str(qre_name).upper():
                    # str_query = f"var_name.str.contains('^{qre_name[1:]}[0-9]+$')"
                    str_query = f"var_name.str.contains('^{qre_name[1:]}_[0-9]+$')"
                else:
                    str_query = f"var_name.str.contains('^{qre_name[1:]}_[0-9]+$')"

                lst_qre_ma_name = df_info.query(str_query)['var_name'].values.tolist()

                if tpl_cat[0].upper() == 'TOTAL':
                    return [qre_lbl, tpl_cat[1], f"({' | '.join([f'{i} > 0' for i in lst_qre_ma_name])})"]

                return [qre_lbl, tpl_cat[1], f"({' | '.join([f'{i} == {tpl_cat[0]}' for i in lst_qre_ma_name])})"]



            if tpl_cat[0].upper() == 'TOTAL':
                return [qre_lbl, tpl_cat[1], f"({qre_name} > 0)"]

            if '@' in qre_name:
                return [qre_lbl, tpl_cat[1], tpl_cat[0]]

            return [qre_lbl, tpl_cat[1], f"({qre_name} == {tpl_cat[0]})"]



        def combine_df_header_by_level(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:

            df_a_repeat = pd.DataFrame(np.repeat(df_a.values, df_b.shape[0], axis=0), columns=df_a.columns)
            df_b_repeat = pd.DataFrame(np.repeat(df_b.values, df_a.shape[0], axis=0), columns=df_b.columns)

            df_b_repeat['idx1'] = df_b_repeat.index % df_a.shape[0]
            df_b_repeat['idx2'] = df_b_repeat.index
            df_b_repeat = df_b_repeat.sort_values(by=['idx1', 'idx2']).reset_index(drop=True).drop(columns=['idx1', 'idx2'])

            df_combine = pd.concat([df_a_repeat, df_b_repeat], axis=1)

            return df_combine


        df_header = pd.DataFrame()

        for i, item in enumerate(lst_header_qres):

            df_qre = pd.DataFrame()
            last_lvl = len(lst_header_qres) - 1

            for j, qre in enumerate(item):

                if len(qre.get('cats')) == 0:
                    qre['cats'] = get_cats_by_qre_name(qre['qre_name'])

                qre.update({'header_info': []})

                for cat in qre['cats'].items():

                    if i == last_lvl:
                        lst_header_info = [len(qre['cats'].keys())] + get_header_query_by_cats(qre['qre_name'], qre['qre_lbl'], cat)
                    else:
                        lst_header_info = [j] + get_header_query_by_cats(qre['qre_name'], qre['qre_lbl'], cat)

                    qre['header_info'].append(lst_header_info)

                df_qre_temp = pd.DataFrame(columns=[f'group_{i}', f'label_{i}', f'code_{i}', f'query_{i}'], data=qre['header_info'])
                df_qre = pd.concat([df_qre, df_qre_temp], axis=0)


            if df_header.empty:
                df_header = df_qre
            else:
                df_header = combine_df_header_by_level(df_header, df_qre)


        df_header['header_group'] = header_group

        lst_col = list(df_header.columns)
        lst_col = lst_col[-1:] + lst_col[:-1]

        df_header = df_header[lst_col]

        # COMBINE QUERY COLUMNS-----------------------------------------------------------------------------------------
        df_header.loc[:, ['query_combined']] = df_header.filter(regex='^query_[0-9]$').agg(' & '.join, axis=1)

        return df_header



    def create_df_tbl_horizontal(self, *, dict_header_qres: dict, df_info: pd.DataFrame) -> pd.DataFrame:

        df_tbl_horizontal = pd.DataFrame()
        int_last_lvl = int()

        for idx, (key_header, val_header) in enumerate(dict_header_qres.items()):
            lst_header_qres = val_header
            int_last_lvl = len(lst_header_qres) - 1

            df_tbl_horizontal = pd.concat([df_tbl_horizontal, self.convert_table_header_to_dataframe(header_group=idx, lst_header_qres=lst_header_qres, df_info=df_info)], axis=0, ignore_index=True)


        idx = 0
        int_order = 0
        while idx < df_tbl_horizontal.shape[0]:
            step = df_tbl_horizontal.at[idx, f'group_{int_last_lvl}']
            df_tbl_horizontal.loc[idx: idx + step - 1, f'group_{int_last_lvl}'] = int_order
            idx += step
            int_order += 1

        df_tbl_horizontal['group_last'] = df_tbl_horizontal[f'group_{int_last_lvl}']



        # if idx == len(dict_header_qres) - 1 and len(lst_header_qres) > 1:
        #
        #     # ADD GROUP_[last level]------------------------------------------------------------------------------------
        #     last_lvl = len(lst_header_qres) - 1
        #     lst_level_count_cats = list()
        #
        #     for qre in lst_header_qres[-1]:
        #         lst_level_count_cats.append(len(qre['cats'].keys()))
        #
        #     idx_min = 0
        #     idx_max = sum(lst_level_count_cats) - 1
        #
        #     for i in range(0, int(df_tbl_horizontal.shape[0] / sum(lst_level_count_cats)) * 2, 2):
        #         df_tbl_horizontal.loc[idx_min:idx_max, f'group_{last_lvl}'] = df_tbl_horizontal.loc[idx_min:idx_max, f'group_{last_lvl}'] + i
        #         idx_min = idx_max + 1
        #         idx_max = idx_max + sum(lst_level_count_cats)
        #
        #     df_tbl_horizontal[f'group_{last_lvl}'] = df_tbl_horizontal[f'group_{last_lvl}'].astype(int)
        #
        #
        #     # ADD GROUP_[before last level]-----------------------------------------------------------------------------
        #
        #     for ilvl in range(len(lst_header_qres) - 1):
        #
        #         if ilvl > 0:
        #             df_tbl_horizontal[f'group_{ilvl}'] = df_tbl_horizontal[[f'label_{ilvl - 1}', f'label_{ilvl}']].agg('|'.join, axis=1)
        #         else:
        #             df_tbl_horizontal[f'group_{ilvl}'] = df_tbl_horizontal[f'label_{ilvl}']
        #
        #
        #         lst_val_label = df_tbl_horizontal[f'group_{ilvl}'].drop_duplicates(keep='first').values.tolist()
        #         df_tbl_horizontal[f'group_{ilvl}'] = df_tbl_horizontal[f'group_{ilvl}'].replace({v: i for i, v in enumerate(lst_val_label)})


        return df_tbl_horizontal



    @staticmethod
    def create_df_tbl_vertical(*, lst_side_qres: list, df_info: pd.DataFrame, str_weighted_var: str) -> pd.DataFrame:

        dict_vertical_qre = {
            'index': list(),
            'name': list(),
            'label': list(),
            'type': list(),
            'cats': list(),
            'cats_unnetted': list(),
            'filter': list(),
            'lst_data_col': list(),
            'mean': list(),
            'sort': list(),
            'calculate': list(),
            'friedman': list(),
            'weight_var': list(),
        }

        for idx, qre in enumerate(lst_side_qres):

            match qre['qre_name']:
                case _ if '$' in qre['qre_name']:  # MA | RANK
                    str_query = f"var_name.str.contains('^{qre['qre_name'][1:]}{'' if '_RANK_' in str(qre['qre_name']).upper() else '_'}[0-9]+$')"
                    lst_data_col = df_info.loc[df_info.eval(str_query), 'var_name'].values.tolist()
                    str_name = qre['qre_name'].replace('$', '')

                case _ if '#combine' in qre['qre_name']:  # QUERY
                    str_name, str_comb = qre['qre_name'].split('#combine')
                    lst_data_col = str_comb.replace('(', '').replace(')', '').replace(' ', '').split(',').strip()

                case _:  # SA | NUM | FT
                    str_name = qre['qre_name']
                    lst_data_col = [str_name]


            df_info_by_qre = df_info.loc[df_info.eval(f"var_name.isin(@lst_data_col)"), :]

            match df_info_by_qre['var_type'].values[0]:

                case 'NUM':
                    dict_cats_default = {
                        'mean': 'Mean',
                        'std': 'Std',
                        'min': 'Minimum',
                        'max': 'Maximum',
                        '25%': 'Quantile 25%',
                        '50%': 'Quantile 50%',
                        '75%': 'Quantile 75%',
                    }

                case _:
                    dict_cats_default = df_info_by_qre['val_lbl'].values[0]


            dict_vertical_qre['index'].append(idx)
            dict_vertical_qre['name'].append(str_name)
            dict_vertical_qre['label'].append(df_info_by_qre['var_lbl'].values[0])
            dict_vertical_qre['type'].append(df_info_by_qre['var_type'].values[0])
            dict_vertical_qre['cats'].append(qre['cats'] if qre.get('cats') else dict_cats_default)
            dict_vertical_qre['cats_unnetted'].append(df_info_by_qre['val_lbl_unnetted'].values[0])
            dict_vertical_qre['filter'].append(qre['qre_filter'] if qre.get('qre_filter') else "")
            dict_vertical_qre['lst_data_col'].append(lst_data_col)
            dict_vertical_qre['mean'].append(qre['mean'] if qre.get('mean') else {})
            dict_vertical_qre['sort'].append(qre['sort'] if qre.get('sort') else "")
            dict_vertical_qre['calculate'].append(qre['calculate'] if qre.get('calculate') else {})
            dict_vertical_qre['friedman'].append(qre['friedman'] if qre.get('friedman') else {})
            dict_vertical_qre['weight_var'].append(str_weighted_var)

        # HERE: break down by cats (add factor if mean is noted)
        # HERE
        
        




        df_tbl_vertical = pd.DataFrame.from_dict(dict_vertical_qre)


        return df_tbl_vertical




    def generate_table(self, *, dict_table: dict) -> list:

        pd.set_option('future.no_silent_downcasting', True)

        # Create df_data with tbl_filter--------------------------------------------------------------------------------
        df_data_filter = self.df_data.query(dict_table['tbl_filter']).copy() if dict_table.get('tbl_filter') else self.df_data.copy()

        # Create df_tbl_horizontal--------------------------------------------------------------------------------------
        df_tbl_horizontal = self.create_df_tbl_horizontal(dict_header_qres=dict_table['dict_header_qres'], df_info=self.df_info)

        # Create df_tbl_vertical----------------------------------------------------------------------------------------
        df_tbl_vertical = self.create_df_tbl_vertical(lst_side_qres=dict_table['lst_side_qres'], df_info=self.df_info, str_weighted_var=dict_table['weight_var'])


        # Data frame contain data table---------------------------------------------------------------------------------
        df_table_count = pd.DataFrame(columns=df_tbl_horizontal.index, data=[])
        df_table_pct = pd.DataFrame(columns=df_tbl_horizontal.index, data=[])
        df_table_sig = pd.DataFrame(columns=df_tbl_horizontal.index, data=[])




        # Iterate each question in 'df_tbl_vertical' then crosstab with 'df_tbl_horizontal'
        here = 1

        def crosstab_vertical_horizontal(sr_qre: pd.Series) -> pd.DataFrame:

            a0 = df_data_filter[sr_qre.lst_data_col].melt().dropna(subset='value')
            a1 = a0[['value']].astype(int).astype(str).value_counts(sort=False)


            return df_tbl_horizontal.code_1



        df_table_count = df_tbl_vertical.apply(crosstab_vertical_horizontal, axis=1)




        # for testing---------------------------------------------------------------------------------------------------
        df_tbl_horizontal.to_excel('df_tbl_horizontal.xlsx')
        df_tbl_vertical.to_excel('df_tbl_vertical.xlsx')
        df_table_count.to_excel('df_table_count.xlsx')
        df_table_pct.to_excel('df_table_pct.xlsx')
        df_table_sig.to_excel('df_table_sig.xlsx')
        # for testing---------------------------------------------------------------------------------------------------


        return list()



        # for grp_hd in lst_group_header:
        #
        #     tbl_info_sig = {
        #         'tbl_name': tbl['tbl_name'],
        #         'is_count': tbl['is_count'],
        #         'is_pct_sign': tbl['is_pct_sign'],
        #         'sig_test_info': tbl['sig_test_info'],
        #         'dict_grp_header': grp_hd,
        #         'weight_var': tbl.get('weight_var') if tbl.get('weight_var') else ''
        #     }
        #
        #     df_temp = self.run_standard_header_sig(df_data, df_info, tbl_info_sig=tbl_info_sig)
        #
        #     if df_tbl.empty:
        #         df_tbl = df_temp
        #     else:
        #         lst_col_temp_to_add = list(df_temp.columns)[6:]
        #         df_tbl = pd.concat([df_tbl, df_temp[lst_col_temp_to_add]], axis=1)
        #
        # # drop row which have all value is nan
        # df_tbl = df_tbl.dropna(how='all')
        #
        #
        # return [tbl['tbl_name'], df_tbl]




