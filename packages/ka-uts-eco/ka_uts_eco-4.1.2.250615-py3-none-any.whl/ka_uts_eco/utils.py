"""
This module provides utility classes for the management of OmniTracker
EcoVadis NHRR (Nachhaltigkeits Risiko Rating) processing for Department UMH
"""
from __future__ import annotations
from typing import Any, TypeAlias

import pandas as pd
import numpy as np

from ka_uts_aod.aod import AoD
from ka_uts_dic.dic import Dic
from ka_uts_dic.doa import DoA
from ka_uts_dic.doaod import DoAoD
from ka_uts_dfr.pddf import PdDf
from ka_uts_log.log import Log

from ka_uts_eco.cfg.utils import CfgUtils as Cfg

TyPdDf: TypeAlias = pd.DataFrame

TyArr = list[Any]
TyAoStr = list[str]
TyBool = bool
TyDic = dict[Any, Any]
TyAoA = list[TyArr]
TyAoD = list[TyDic]
TyDoAoA = dict[Any, TyAoA]
TyDoAoD = dict[Any, TyAoD]
TyDoB = dict[Any, bool]
TyAoD_DoAoD = TyAoD | TyDoAoD
TyTup = tuple[Any]
TyTask = Any
TyDoPdDf = dict[Any, TyPdDf]
TyPdDf_DoPdDf = TyPdDf | TyDoPdDf
TyToAoDDoAoD = tuple[TyAoD, TyDoAoD]

TnDic = None | TyDic
TnAoD = None | TyAoD
TnDoAoA = None | TyDoAoA
TnDoAoD = None | TyDoAoD
TnPdDf = None | TyPdDf
TnStr = None | str


class Evup:
    """
    EcoVadis Upload class
    """
    @staticmethod
    def sh_aod_evup_adm(doaod: TyDoAoD, operation: str) -> TyAoD:
        """
        Show array of dictionaries for admin function for evup
        """
        match operation:
            case 'CU', 'CUD':
                aod: TyAoD = DoAoD.union_by_keys(doaod, ['new', 'ch_y'])
            case 'C', 'CD':
                aod = DoAoD.union_by_keys(doaod, ['new'])
            case 'U', 'UD':
                aod = DoAoD.union_by_keys(doaod, ['ch_y'])
            case _:
                aod = DoAoD.union(doaod)
        return aod


class Evex:
    """
    EcoVadis Export class
    """
    @staticmethod
    def sh_d_evex(df_evex: TnPdDf) -> TyDic:
        if df_evex is None:
            return {}
        _df_evex = df_evex.replace(to_replace=np.nan, value=None, inplace=False)
        _aod = _df_evex.to_dict(orient='records')
        if len(_aod) == 1:
            d_evex: TyDic = _aod[0]
            return d_evex
        msg = "Evex Dataframe: {F} contains multiple records: {R}"
        Log.error(msg.format(F=df_evex, R=_aod))
        return {}

    @staticmethod
    def sh_d_evup_del_from_dic(d_evex: TnDic) -> TnDic:
        d_evup: TyDic = {}
        if d_evex is None:
            return d_evup
        Dic.set_tgt_with_src_by_d_tgt2src(d_evup, d_evex, Cfg.d_del_evup2evex)
        return d_evup

    @classmethod
    def sh_d_evup_del_from_df(cls, df_evex_row: TyPdDf) -> TnDic:
        _d_evex: TnDic = cls.sh_d_evex(df_evex_row)
        return cls.sh_d_evup_del_from_dic(_d_evex)

    @staticmethod
    def map(aod_evex: TnAoD, d_map_evex: TyDic) -> TyAoD:
        aod_evex_new: TyAoD = []
        if not aod_evex:
            return aod_evex_new
        for dic in aod_evex:
            dic_new = {}
            for key, value in dic.items():
                # dic_new[key] = Cfg.d_ecv_iq2umh_iq.get(value, value)
                dic_new[key] = d_map_evex.get(value, value)
            aod_evex_new.append(dic_new)
        return aod_evex_new


class EvinVerify:
    """
    OmniTracker EcoVadis class
    """
    @staticmethod
    def verify_duns(d_evin: TyDic, doaod_vfy: TyDoAoD) -> tuple[TyBool, TnStr]:
        """
        Verify DUNS number
        """
        _duns: TnStr = Dic.get(d_evin, Cfg.evin_key_duns)
        if not _duns:
            DoA.append_unique_by_key(doaod_vfy, 'duns_is_empty', d_evin)
            return False, _duns
        if not _duns.isdigit():
            DoA.append_unique_by_key(doaod_vfy, 'duns_is_not_numeric', d_evin)
            return False, _duns
        if len(_duns) < 9:
            _duns = f"{_duns:09}"
        return True, _duns

    @staticmethod
    def verify_cmpdinm(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        """
        Verify Company display name
        """
        _cmpdinm = Dic.get(d_evin, Cfg.evin_key_cmpdinm)
        if not _cmpdinm:
            DoA.append_unique_by_key(doaod_vfy, 'cmpdinm_is_empty', d_evin)
            return False
        return True

    @staticmethod
    def verify_regno(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        """
        Verify Registration number
        """
        _cmpdinm = Dic.get(d_evin, Cfg.evin_key_regno)
        if not _cmpdinm:
            DoA.append_unique_by_key(doaod_vfy, 'regno_is_empty', d_evin)
            return False
        return True

    @staticmethod
    def verify_coco(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        _coco: TnStr = Dic.get(d_evin, Cfg.evin_key_coco)
        if not _coco:
            DoA.append_unique_by_key(doaod_vfy, 'coco_is_empty', d_evin)
            return False
        else:
            import pycountry
            try:
                country = pycountry.countries.get(alpha_2=_coco.upper())
            except KeyError:
                DoA.append_unique_by_key(doaod_vfy, 'coco_is_invalid', d_evin)
                return False
        return True

    @staticmethod
    def verify_objectid(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        _objectid = Dic.get(d_evin, Cfg.evin_key_objectid)
        if not _objectid:
            DoA.append_unique_by_key(doaod_vfy, 'objectid_is_empty', d_evin)
            return False
        return True

    @staticmethod
    def verify_town(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        _town: TnStr = Dic.get(d_evin, Cfg.evin_key_town)
        if not _town:
            DoA.append_unique_by_key(doaod_vfy, 'town_is_empty', d_evin)
            return False
        else:
            _coco = Dic.get(d_evin, Cfg.evin_key_coco)
            if not _coco:
                return True
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut
            geolocator = Nominatim(user_agent="geo_verifier")
            try:
                location = geolocator.geocode(_town)
                if location is None:
                    DoA.append_unique_by_key(doaod_vfy, 'town_is_invalid', d_evin)
                else:
                    if _coco.lower() not in location.address.lower():
                        DoA.append_unique_by_key(
                                doaod_vfy, 'town_is_invalid', d_evin)
                        return False
            except GeocoderTimedOut:
                DoA.append_unique_by_key(doaod_vfy, 'town_is_invalid', d_evin)
                return False
        return True

    @staticmethod
    def verify_poco(d_evin: TyDic, doaod_vfy: TyDoAoD) -> TyBool:
        _poco: TnStr = Dic.get(d_evin, Cfg.evin_key_poco)
        if not _poco:
            DoA.append_unique_by_key(doaod_vfy, 'poco_is_empty', d_evin)
            return False
        else:
            _coco = Dic.get(d_evin, Cfg.evin_key_coco)
            from postal_codes_tools.postal_codes import verify_postal_code_format
            if not verify_postal_code_format(postal_code=_poco, country_iso2=_coco):
                DoA.append_unique_by_key(doaod_vfy, 'poco_is_invalid', d_evin)
                return False
        return True

    @classmethod
    def verify_d_evin(
            cls, d_evin: TyDic, doaod_vfy: TyDoAoD, kwargs: TyDic
    ) -> TyBool:
        # Set verification summary switch
        _d_sw: TyDoB = {}
        # _sw: TyBool = True

        # Verify DUNS
        _sw_vfy_duns = kwargs.get('sw_vfy_duns', True)
        if _sw_vfy_duns:
            _d_sw['duns'], _duns = cls.verify_duns(d_evin, doaod_vfy)
            Dic.set_by_key(d_evin, Cfg.evin_key_duns, _duns)

        # Verify Country display name
        _sw_vfy_cmpdinm = kwargs.get('sw_vfy_cmpdinm', True)
        if _sw_vfy_cmpdinm:
            _d_sw['cmpdinm'] = cls.verify_cmpdinm(d_evin, doaod_vfy)

        # Verify Country display name
        _sw_vfy_regno = kwargs.get('sw_vfy_regno', True)
        if _sw_vfy_regno:
            _d_sw['regno'] = cls.verify_regno(d_evin, doaod_vfy)

        # Verify Country Code
        _sw_vfy_coco = kwargs.get('sw_vfy_coco', True)
        if _sw_vfy_coco:
            _d_sw['coco'] = cls.verify_coco(d_evin, doaod_vfy)

        # Verify ObjectID
        _sw_vfy_objectid = kwargs.get('sw_vfy_objectid', True)
        if _sw_vfy_objectid:
            _d_sw['objectid'] = cls.verify_objectid(d_evin, doaod_vfy)

        # Verify Town in Country
        _sw_vfy_town = kwargs.get('sw_vfy_town', False)
        if _sw_vfy_town:
            _d_sw['town'] = cls.verify_town(d_evin, doaod_vfy)

        # Verify Postal Code
        _sw_vfy_poco = kwargs.get('sw_vfy_poco', True)
        if _sw_vfy_poco:
            _d_sw['poco'] = cls.verify_poco(d_evin, doaod_vfy)

        # _sw_ignore_vfy = kwargs.get('sw_ignore_vfy', True)
        # _sw_ignore_vfy_duns = kwargs.get('sw_ignore_vfy_duns', True)
        _sw_use_duns = kwargs.get('sw_use_duns', True)
        if _sw_use_duns:
            return _d_sw['duns'] and _d_sw['cmpdinm']

        if (_d_sw['duns'] and _d_sw['cmpdinm']) or \
           (_d_sw['regno'] and _d_sw['coco'] and _d_sw['cmpdinm']) or \
           (_d_sw['cmpnm'] and _d_sw['coco'] and _d_sw['cmpdinm']):
            return True

        return False

    @classmethod
    def verify_aod_evin(
            cls, aod_evin, doaod_vfy, kwargs: TyDic
    ) -> TyAoD:
        _aod_evin: TyAoD = []
        for _d_evin in aod_evin:
            _sw: bool = cls.verify_d_evin(_d_evin, doaod_vfy, kwargs)
            if _sw:
                _aod_evin.append(_d_evin)
        return _aod_evin


class Evin:
    """
    EcoVadis input data (from Systems like OmniTracker) class
    """

    @staticmethod
    def sh_d_evup_adm(d_evin: TyDic) -> TyDic:
        d_evup: TyDic = {}
        Dic.set_tgt_with_src(d_evup, Cfg.d_evup2const)
        Dic.set_tgt_with_src_by_d_tgt2src(d_evup, d_evin, Cfg.d_evup2evin)
        return d_evup

    @classmethod
    def sh_aod_evup_adm(cls, aod_evin) -> TyAoD:
        _aod_evup: TyAoD = []
        for _d_evin in aod_evin:
            AoD.append_unique(_aod_evup, Evin.sh_d_evup_adm(_d_evin))
        return _aod_evup

    @classmethod
    def sh_doaod_adm_new(cls, aod_evin) -> TyDoAoD:
        _doaod_evup: TyDoAoD = {}
        for _d_evin in aod_evin:
            _d_evup = cls.sh_d_evup_adm(_d_evin)
            DoA.append_unique_by_key(_doaod_evup, 'new', _d_evup)
        return _doaod_evup


class EvinEvex:
    """
    Check EcoVadis input data (from Systems like OmniTracker) against
    EcoVadis export data
    """
    msg_evex = ("No entries found in Evex dataframe for "
                "Evex key: '{K1}' and Evin value: {V1} and "
                "Evex key: '{K2}' and Evin value: {V2}")
    msg_evin = "Evin Key: '{K}' not found in Evin Dictionary {D}"

    @classmethod
    def query_with_key(
            cls, d_evin: TyDic, df_evex: TnPdDf, evin_key: Any, evin_value_cc: Any
    ) -> TnPdDf:
        evin_value = Dic.get(d_evin, evin_key)
        if not df_evex:
            return None
        if evin_value:
            evex_key = Cfg.d_evin2evex_keys[evin_key]
            condition = (df_evex[evex_key] == evin_value) & (df_evex[Cfg.evex_key_cc] == evin_value_cc)
            df: TnPdDf = df_evex.loc[condition]
            Log.info(cls.msg_evex.format(
                K1=evex_key, V1=evin_value, K2=Cfg.evex_key_cc, V2=evin_value_cc))
            return df
        else:
            Log.debug(cls.msg_evin.format(K=evin_key, D=d_evin))
            return None

    @classmethod
    def query_with_keys(cls, d_evin: TyDic, df_evex: TnPdDf) -> TnPdDf:
        evin_value_cc = d_evin.get(Cfg.evin_key_cc)
        if not evin_value_cc:
            Log.error(cls.msg_evin.format(K=Cfg.evin_key_cc, D=d_evin))
            return None
        for evin_key in Cfg.a_evin_key:
            df = cls.query_with_key(d_evin, df_evex, evin_key, evin_value_cc)
            if df is not None:
                return df
        return None

    @classmethod
    def query(cls, d_evin: TyDic, df_evex: TnPdDf) -> TyDic:
        _df: TnPdDf = PdDf.query_with_key(
            df_evex, d_evin,
            dic_key=Cfg.evin_key_objectid, d_key2key=Cfg.d_evin2evex_keys)
        if _df is not None:
            return Evex.sh_d_evex(_df)

        _df = PdDf.query_with_key(
            df_evex, d_evin,
            dic_key=Cfg.evin_key_duns, d_key2key=Cfg.d_evin2evex_keys)
        if _df is not None:
            return Evex.sh_d_evex(_df)

        _df = cls.query_with_keys(d_evin, df_evex)
        return Evex.sh_d_evex(_df)

    @classmethod
    def join_adm(
            cls, aod_evin: TnAoD, df_evex: TnPdDf, doaod_vfy: TyDoAoD, sw_ch_n: TyBool
    ) -> TyDoAoD:
        if not aod_evin:
            return {}
        if df_evex is None:
            return Evin.sh_doaod_adm_new(aod_evin)

        _doaod_evup: TyDoAoD = {}
        for _d_evin in aod_evin:
            _df: TnPdDf = PdDf.query_with_key(
                    df_evex, _d_evin,
                    dic_key=Cfg.evin_key_objectid, d_key2key=Cfg.d_evin2evex_keys)
            if _df is None:
                DoA.append_unique_by_key(doaod_vfy, 'adm_evin2evex_new', _d_evin)
                _d_evup = Evin.sh_d_evup_adm(_d_evin)
                DoA.append_unique_by_key(_doaod_evup, 'new', _d_evup)
            else:
                DoA.append_unique_by_key(doaod_vfy, 'adm_evin2evex_old', _d_evin)
                _d_evex = Evex.sh_d_evex(_df)
                _change_status, _d_evup = cls.sh_d_evup_adm(_d_evin, _d_evex, sw_ch_n)
                DoA.append_unique_by_key(_doaod_evup, _change_status, _d_evup)

        return _doaod_evup

    @classmethod
    def join_del(
            cls, aod_evin: TnAoD, df_evex: TnPdDf, doaod_vfy: TyDoAoD
    ) -> TyAoD:
        _aod_evup: TyAoD = []
        if not aod_evin:
            return _aod_evup

        for _d_evin in aod_evin:
            _df_evex_row: TnPdDf = PdDf.query_with_key(
                    df_evex, _d_evin,
                    dic_key=Cfg.evin_key_objectid,
                    d_key2key=Cfg.d_evin2evex_keys)
            if _df_evex_row is None:
                DoA.append_unique_by_key(doaod_vfy, 'del_evin2evex_n', _d_evin)
            else:
                DoA.append_unique_by_key(doaod_vfy, 'del_evin2evex_y', _d_evin)
                _d_evup_del: TnDic = Evex.sh_d_evup_del_from_df(_df_evex_row)
                if _d_evup_del:
                    AoD.append_unique(_aod_evup, _d_evup_del)
        return _aod_evup

    @staticmethod
    def sh_d_evup_adm(
            d_evin: TyDic, d_evex: TyDic, sw_ch_n: TyBool) -> tuple[str, TyDic]:
        d_evup: TyDic = {}
        Dic.set_tgt_with_src(d_evup, Cfg.d_evup2const)
        Dic.set_tgt_with_src_by_d_tgt2src(d_evup, d_evex, Cfg.d_evup2evex)
        Dic.set_tgt_with_src_by_d_tgt2src(d_evup, d_evin, Cfg.d_evup2evin)
        change_status = 'ch_n'
        if sw_ch_n:
            return change_status, d_evup
        for key_evin, key_evex in Cfg.d_evin2evex.items():
            if d_evin[key_evin] != d_evex[key_evex]:
                key_evup = Cfg.d_evin2evup[key_evin]
                d_evup[key_evup] = d_evin[key_evin]
                change_status = 'ch_y'
        return change_status, d_evup


class EvexEvin:
    """
    Check EcoVadis Export Data against
    EcoVadis input data (from Systems like OmniTracker)
    """
    @classmethod
    def join_del(
            cls, aod_evex: TnAoD, df_evin: TnPdDf, doaod_vfy: TyDoAoD
    ) -> TyAoD:
        _aod_evup: TyAoD = []
        if not aod_evex or df_evin is None:
            return _aod_evup
        for _d_evex in aod_evex:
            _df_evin_row: TnPdDf = PdDf.query_with_key(
                    df_evin, _d_evex,
                    dic_key=Cfg.evin_key_objectid, d_key2key=Cfg.d_evex2evin_keys)
            if _df_evin_row is None:
                DoA.append_unique_by_key(doaod_vfy, 'del_evex2evin_n', _d_evex)
                _d_evup = Evex.sh_d_evup_del_from_dic(_d_evex)
                if _d_evup:
                    AoD.append_unique(_aod_evup, _d_evup)
            else:
                DoA.append_unique_by_key(doaod_vfy, 'del_evex2evin_y', _d_evex)
        return _aod_evup
