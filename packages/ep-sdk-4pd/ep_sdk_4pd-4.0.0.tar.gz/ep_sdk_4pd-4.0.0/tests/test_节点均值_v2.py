import datetime
import pickle
import requests
import os
from copy import deepcopy
import logging

import lightgbm as lgb
import numpy as np
import pandas as pd
import holidays
import tempfile
#
#
from ep_sdk_4pd.ep_system import EpSystem
from ep_sdk_4pd.ep_data import EpData

#


logger = logging.getLogger(__name__)

EARLY_STOP_ROUNDS = 30
#
# lr = 0.3
params = {
    # "min_data_in_bin": 5,
    #
    'num_leaves': 5,
    'min_data_in_leaf': 30,
    'objective': 'regression',
    'max_depth': 4,
    'learning_rate': 0.1,
    "boosting": "gbdt",
    "feature_fraction": 0.8,
    "bagging_fraction": 0.2,
    "bagging_freq": 1,
    "bagging_seed": 1,
    "metric": 'mse',
    "lambda_l1": 0.5,
    "lambda_l2": 1,
    "random_state": 1022,
    "num_threads": -1,
    'verbose': 0,
    #
    'early_stopping_round': EARLY_STOP_ROUNDS,
}


#
def simple_reg_price(train, train_label, test, test_label, cate_fea=[], lr=0.3):
    #
    #
    dtrain = lgb.Dataset(train, train_label, categorical_feature=cate_fea, free_raw_data=False)
    dval = lgb.Dataset(test, test_label, categorical_feature=cate_fea, reference=dtrain, free_raw_data=False)
    #
    params['learning_rate'] = lr
    model = lgb.train(
        params,
        dtrain,
        num_boost_round=500,
        # feval=calc_wauc,
        valid_sets=[dtrain, dval],
        # verbose_eval=10,
        # early_stopping_rounds=EARLY_STOP_ROUNDS
    )
    #
    valid_prob = model.predict(test)
    train_prob = model.predict(train)

    return valid_prob, train_prob, model


#
#
def eval_reg_price(train, train_label, num_round, cate_fea=[], lr=0.3):
    #
    dtrain = lgb.Dataset(train, train_label, categorical_feature=cate_fea, free_raw_data=False)
    #
    #
    eval_param = deepcopy(params)
    eval_param.pop("early_stopping_round")
    eval_param['learning_rate'] = lr
    #
    model = lgb.train(
        eval_param,
        dtrain,
        num_boost_round=num_round,
        # # feval=calc_wauc,
        # valid_sets=[dtrain,dval],
        # # verbose_eval=10,
        # # early_stopping_rounds=EARLY_STOP_ROUNDS
    )
    #
    return model


#


def get_data_label(market, power, weather=None, istrain=False):
    #
    #
    float_names = ["win_out", "sun_out", "tongdiao", "lianluo"] \
                  + ["bwin_out", "bsun_out", "btongdiao", "blianluo"] \
                  + ["bshui_huo", "shui_huo"] \
                  + ["real_fact_price", "before_fact_price"] \
                  + ["idx"] \
                  + ["power_pred"] \
                  + ["before_smooth_5", "real_smooth_5"] \
                  + ["feng_riqian_10", "guang_riqian_10", "tong_riqian_10", "lian_riqian_10", "feng_shiji_10",
                     "guang_shiji_10", "tong_shiji_10", "lian_shiji_10"] \
                  + ["shuihuo_riqian_10", "shuihuo_shiji_10"] \
                  + ["feng_riqian_5", "guang_riqian_5", "tong_riqian_5", "lian_riqian_5", "feng_shiji_5",
                     "guang_shiji_5", "tong_shiji_5", "lian_shiji_5"] \
                  + ["shuihuo_riqian_5", "shuihuo_shiji_5"] \
                  + ["feng_riqian_3", "guang_riqian_3", "tong_riqian_3", "lian_riqian_3", "feng_shiji_3",
                     "guang_shiji_3", "tong_shiji_3", "lian_shiji_3"] \
                  + ["shuihuo_riqian_3", "shuihuo_shiji_3"] \
        #
    #
    weather = [row for idx, row in weather.iterrows()]
    date_weather = {
        row["timestamp"]: row for row in weather
    }
    wea_keys = list(sorted([key for key in weather[0].keys() if key != "timestamp"]))
    #
    #
    float_names = float_names + wea_keys
    #
    price_names = ["before_price", "real_price", "diff_price"] + ["power_fact"] if istrain else []
    #
    all_datas = {
        name: [] for name in ["datetime"] + float_names + price_names
        #
    }
    power_pred = power["predicted_power"].tolist()
    #
    power_fact = power["power"].tolist() if istrain else []
    #
    # weather = [row for idx, row in weather.iterrows()] if weather is not None else []
    #
    for idx, row in market.iterrows():
        if istrain:
            if idx < 96 * 3:
                continue
        #
        sup_now = market.iloc[idx]
        sup_before = market.iloc[idx]
        if istrain:
            sup_before = market.iloc[idx - 96 * 2]
        #
        #
        #
        time_str = str(sup_now['timestamp']).strip()
        date_part, time_part = time_str.split(' ')
        if time_part == '24:00':
            day = datetime.datetime.strptime(date_part, '%Y-%m-%d') + datetime.timedelta(days=1)
            day = day.replace(hour=0, minute=0, second=0)
        else:
            day = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        #
        # pre_day = day - datetime.timedelta(days=2)
        # date_str = datetime.datetime.strftime(pre_day, '%Y-%m-%d %H:%M:%S')[:10]
        date_str = time_str[:10]
        wea_data = date_weather[date_str]
        for key in wea_keys:
            all_datas[key].append(wea_data[key])
        #
        #
        day_now = datetime.datetime.strftime(day, '%Y-%m-%d %H:%M:%S')
        all_datas["datetime"].append(day_now)
        #
        #
        #
        all_datas["bwin_out"].append(sup_before['wind_power_day_ahead'])
        all_datas["bsun_out"].append(sup_before['pv_power_day_ahead'])
        all_datas["btongdiao"].append(sup_before['provincial_load_forecast'])
        all_datas["blianluo"].append(-sup_before['day_ahead_tieline_power'])
        all_datas["bshui_huo"].append(
            sup_before['provincial_load_forecast'] - sup_before['day_ahead_tieline_power'] - sup_before[
                'pv_power_day_ahead'] - sup_before['wind_power_day_ahead'])
        #
        #
        all_datas["win_out"].append(sup_before['wind_power_actual_value'])
        all_datas["sun_out"].append(sup_before['pv_actual_value'])
        all_datas["tongdiao"].append(sup_before['system_load_actual_value'])
        all_datas["lianluo"].append(-sup_before['tie_line_out_actual_value'])
        all_datas["shui_huo"].append(
            sup_before['system_load_actual_value'] - sup_before['tie_line_out_actual_value'] - sup_before[
                'pv_actual_value'] - sup_before['wind_power_actual_value'])
        #
        all_datas["before_fact_price"].append(sup_before['day_ahead_price'])
        all_datas["real_fact_price"].append(sup_before['electricity_price'])
        all_datas["idx"].append(idx % 96)
        all_datas["power_pred"].append(power_pred[idx])
        # #
        all_datas["before_smooth_5"].append(sup_before["before_smooth_5"])
        all_datas["real_smooth_5"].append(sup_before["real_smooth_5"])
        #
        #
        all_datas["feng_riqian_10"].append(sup_before["feng_riqian_10"])
        all_datas["guang_riqian_10"].append(sup_before["guang_riqian_10"])
        all_datas["tong_riqian_10"].append(sup_before["tong_riqian_10"])
        all_datas["lian_riqian_10"].append(sup_before["lian_riqian_10"])
        all_datas["shuihuo_riqian_10"].append(
            sup_before["tong_riqian_10"] - sup_before["lian_riqian_10"] - sup_before["feng_riqian_10"] - sup_before[
                "guang_riqian_10"])
        all_datas["feng_shiji_10"].append(sup_before["feng_shiji_10"])
        all_datas["guang_shiji_10"].append(sup_before["guang_shiji_10"])
        all_datas["tong_shiji_10"].append(sup_before["tong_shiji_10"])
        all_datas["lian_shiji_10"].append(sup_before["lian_shiji_10"])
        all_datas["shuihuo_shiji_10"].append(
            sup_before["tong_shiji_10"] - sup_before["lian_shiji_10"] - sup_before["feng_shiji_10"] - sup_before[
                "guang_shiji_10"])
        #
        all_datas["feng_riqian_5"].append(sup_before["feng_riqian_5"])
        all_datas["guang_riqian_5"].append(sup_before["guang_riqian_5"])
        all_datas["tong_riqian_5"].append(sup_before["tong_riqian_5"])
        all_datas["lian_riqian_5"].append(sup_before["lian_riqian_5"])
        all_datas["shuihuo_riqian_5"].append(
            sup_before["tong_riqian_5"] - sup_before["lian_riqian_5"] - sup_before["feng_riqian_5"] - sup_before[
                "guang_riqian_5"])
        all_datas["feng_shiji_5"].append(sup_before["feng_shiji_5"])
        all_datas["guang_shiji_5"].append(sup_before["guang_shiji_5"])
        all_datas["tong_shiji_5"].append(sup_before["tong_shiji_5"])
        all_datas["lian_shiji_5"].append(sup_before["lian_shiji_5"])
        all_datas["shuihuo_shiji_5"].append(
            sup_before["tong_shiji_5"] - sup_before["lian_shiji_5"] - sup_before["feng_shiji_5"] - sup_before[
                "guang_shiji_5"])
        #
        all_datas["feng_riqian_3"].append(sup_before["feng_riqian_3"])
        all_datas["guang_riqian_3"].append(sup_before["guang_riqian_3"])
        all_datas["tong_riqian_3"].append(sup_before["tong_riqian_3"])
        all_datas["lian_riqian_3"].append(sup_before["lian_riqian_3"])
        all_datas["shuihuo_riqian_3"].append(
            sup_before["tong_riqian_3"] - sup_before["lian_riqian_3"] - sup_before["feng_riqian_3"] - sup_before[
                "guang_riqian_3"])
        all_datas["feng_shiji_3"].append(sup_before["feng_shiji_3"])
        all_datas["guang_shiji_3"].append(sup_before["guang_shiji_3"])
        all_datas["tong_shiji_3"].append(sup_before["tong_shiji_3"])
        all_datas["lian_shiji_3"].append(sup_before["lian_shiji_3"])
        all_datas["shuihuo_shiji_3"].append(
            sup_before["tong_shiji_3"] - sup_before["lian_shiji_3"] - sup_before["feng_shiji_3"] - sup_before[
                "guang_shiji_3"])
        #
        #
        #
        if istrain:
            all_datas["power_fact"].append(power_fact[idx])
            all_datas["before_price"].append(sup_now['day_ahead_price'])
            all_datas["real_price"].append(sup_now['electricity_price'])
            all_datas["diff_price"].append(sup_now['day_ahead_price'] - sup_now['electricity_price'])
        #
    #
    #
    float_names = [name for name in float_names if name not in []]
    # float_names = [name for name in float_names if name not in ["power_pred"]]
    cate_names = []
    #
    all_datas = pd.DataFrame(all_datas)
    #
    all_datas["datetime"] = all_datas["datetime"].apply(
        lambda x: datetime.datetime.strptime(str(x).strip(), '%Y-%m-%d %H:%M:%S'))
    #
    all_datas["weekday"] = all_datas["datetime"].apply(lambda x: x.weekday())
    all_datas["hour"] = all_datas["datetime"].apply(lambda x: x.hour)
    all_datas["month"] = all_datas["datetime"].apply(lambda x: x.month)
    all_datas["holiday"] = all_datas["datetime"].apply(lambda x: 1 if x.date() in cn_holidays else 0)
    all_datas["day"] = all_datas["datetime"].apply(lambda x: x.day)
    #
    # all_datas["next_month_first"] = all_datas["datetime"].apply(lambda x: datetime.datetime(x.year, x.month + 1, 1) if x.month != 12 else datetime.datetime(x.year + 1, 1, 1))
    # all_datas["day_to_end"] = all_datas.apply(lambda x: (x["next_month_first"] - datetime.datetime(x["datetime"].year, x["datetime"].month, x["datetime"].day)).days, axis=1)
    #
    date_names = ["weekday", "hour", "month", "holiday"]
    date_names = ["weekday", "hour", "month", "holiday", "day"]
    # date_names = ["weekday", "hour", "month", "holiday", "day", "day_to_end"]
    #
    cate_names = cate_names + date_names
    # float_names = float_names + date_names
    #
    return all_datas, float_names, cate_names


#


def smooth_data(power_fact, wind_half=5):
    datas = []
    for idx in range(len(power_fact)):
        left = max(0, idx - wind_half)
        right = min(len(power_fact), idx + wind_half + 1)
        #
        datas.append(sum(power_fact[left:right]) / (right - left))
    return datas


#


def smooth_data_double(power_fact, date_points=96, wind_half=5):
    if len(power_fact) % date_points != 0:
        return power_fact
    #
    dates_num = len(power_fact) // date_points
    #
    power_fact = power_fact.reshape(-1, date_points)
    #
    logger.info(f"date_points: {dates_num, date_points}")
    #
    power_fact_smooth = [[0.0] * date_points for i in range(dates_num)]
    for idx in range(date_points):
        #
        for idy in range(dates_num):
            left = max(0, idy - wind_half)
            right = min(dates_num, idy + wind_half + 1)
            #
            power_fact_smooth[idy][idx] = sum(power_fact[left:right, idx]) / (right - left)
    #
    power_fact_smooth = np.array(power_fact_smooth).reshape(-1)
    return power_fact_smooth


#


def smooth_data_left(power_fact, date_points=96, wind_half=5):
    if len(power_fact) % date_points != 0:
        return power_fact
    #
    dates_num = len(power_fact) // date_points
    #
    power_fact = power_fact.reshape(-1, date_points)
    #
    logger.info(f"date_points: {dates_num, date_points}")
    #
    power_fact_smooth = [[0.0] * date_points for i in range(dates_num)]
    for idx in range(date_points):
        #
        for idy in range(dates_num):
            left = max(0, idy - wind_half)
            right = idy + 1
            #
            power_fact_smooth[idy][idx] = sum(power_fact[left:right, idx]) / (right - left)
    #
    power_fact_smooth = np.array(power_fact_smooth).reshape(-1)
    return power_fact_smooth


#

def smooth_left_data(power_fact, wind_half=5):
    datas = []
    for idx in range(len(power_fact)):
        left = max(0, idx - wind_half)
        # right = min(len(power_fact), idx + wind_half + 1)
        right = idx + 1
        #
        datas.append(sum(power_fact[left:right]) / (right - left))
    return datas


#


def process_market(market, day_point=96):
    #
    # market['day_ahead_price'] = smooth_data_double(market['day_ahead_price'].to_numpy(), date_points=day_point, wind_half=5)
    # market['electricity_price'] = smooth_data_double(market['electricity_price'].to_numpy(), date_points=day_point, wind_half=5)
    #
    market['day_ahead_price'] = smooth_data_left(market['day_ahead_price'].to_numpy(), date_points=day_point,
                                                 wind_half=5)
    market['electricity_price'] = smooth_data_left(market['electricity_price'].to_numpy(), date_points=day_point,
                                                   wind_half=5)
    #
    market['feng_riqian_10'] = smooth_data_left(market['wind_power_day_ahead'].to_numpy(), date_points=day_point,
                                                wind_half=10)
    market['guang_riqian_10'] = smooth_data_left(market['pv_power_day_ahead'].to_numpy(), date_points=day_point,
                                                 wind_half=10)
    market['tong_riqian_10'] = smooth_data_left(market['provincial_load_forecast'].to_numpy(), date_points=day_point,
                                                wind_half=10)
    market['lian_riqian_10'] = smooth_data_left(market['day_ahead_tieline_power'].to_numpy(), date_points=day_point,
                                                wind_half=10)
    #
    market['feng_shiji_10'] = smooth_data_left(market['wind_power_actual_value'].to_numpy(), date_points=day_point,
                                               wind_half=10)
    market['guang_shiji_10'] = smooth_data_left(market['pv_actual_value'].to_numpy(), date_points=day_point,
                                                wind_half=10)
    market['tong_shiji_10'] = smooth_data_left(market['system_load_actual_value'].to_numpy(), date_points=day_point,
                                               wind_half=10)
    market['lian_shiji_10'] = smooth_data_left(market['tie_line_out_actual_value'].to_numpy(), date_points=day_point,
                                               wind_half=10)
    #
    market['feng_riqian_5'] = smooth_data_left(market['wind_power_day_ahead'].to_numpy(), date_points=day_point,
                                               wind_half=5)
    market['guang_riqian_5'] = smooth_data_left(market['pv_power_day_ahead'].to_numpy(), date_points=day_point,
                                                wind_half=5)
    market['tong_riqian_5'] = smooth_data_left(market['provincial_load_forecast'].to_numpy(), date_points=day_point,
                                               wind_half=5)
    market['lian_riqian_5'] = smooth_data_left(market['day_ahead_tieline_power'].to_numpy(), date_points=day_point,
                                               wind_half=5)
    #
    market['feng_shiji_5'] = smooth_data_left(market['wind_power_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=5)
    market['guang_shiji_5'] = smooth_data_left(market['pv_actual_value'].to_numpy(), date_points=day_point, wind_half=5)
    market['tong_shiji_5'] = smooth_data_left(market['system_load_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=5)
    market['lian_shiji_5'] = smooth_data_left(market['tie_line_out_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=5)
    #
    market['feng_riqian_3'] = smooth_data_left(market['wind_power_day_ahead'].to_numpy(), date_points=day_point,
                                               wind_half=3)
    market['guang_riqian_3'] = smooth_data_left(market['pv_power_day_ahead'].to_numpy(), date_points=day_point,
                                                wind_half=3)
    market['tong_riqian_3'] = smooth_data_left(market['provincial_load_forecast'].to_numpy(), date_points=day_point,
                                               wind_half=3)
    market['lian_riqian_3'] = smooth_data_left(market['day_ahead_tieline_power'].to_numpy(), date_points=day_point,
                                               wind_half=3)
    #
    market['feng_shiji_3'] = smooth_data_left(market['wind_power_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=3)
    market['guang_shiji_3'] = smooth_data_left(market['pv_actual_value'].to_numpy(), date_points=day_point, wind_half=3)
    market['tong_shiji_3'] = smooth_data_left(market['system_load_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=3)
    market['lian_shiji_3'] = smooth_data_left(market['tie_line_out_actual_value'].to_numpy(), date_points=day_point,
                                              wind_half=3)
    #
    #
    #
    market['before_smooth_5'] = smooth_data_left(market['day_ahead_price'].to_numpy(), date_points=day_point,
                                                 wind_half=5)
    market['real_smooth_5'] = smooth_data_left(market['electricity_price'].to_numpy(), date_points=day_point,
                                               wind_half=5)
    #
    return market


#

def process_weather(weather):
    timestamps = sorted(list(set([wea['timestamp'] for wea in weather])))
    print(f"timestamps: {len(timestamps), len(weather)}")
    #
    wea_keys = [
        "tem_day",
        "tem_night",
        "win_meter",
        "humidity",
        # "visibility",
        # "pressure",
        # "cloudPct",
    ]

    weather_datas = {"timestamp": []}
    for key in wea_keys:
        #
        weather_datas[f"{key}_max"] = []
        weather_datas[f"{key}_mean"] = []
        #
        for idx in range(10):
            suf = int(idx * 10)
            weather_datas[f"{key}_{suf}"] = []
    #
    for idx, ts in enumerate(timestamps):
        weather_ts = [wea for wea in weather if wea['timestamp'] == ts]
        #
        for key in wea_keys:
            key_data = [wea[key] for wea in weather_ts]
            key_data = sorted(key_data)
            #
            weather_datas[f"{key}_max"].append(key_data[-1])
            weather_datas[f"{key}_mean"].append(sum(key_data) / len(key_data))
            #
            for idx in range(10):
                suf = int(idx * 10)
                weather_datas[f"{key}_{suf}"].append(key_data[int(idx * len(key_data) / 10)])
        #
        weather_datas[f"timestamp"].append(ts[:10])
    #
    weather_datas = pd.DataFrame(weather_datas)
    return weather_datas, wea_keys


#

def train():
    #
    day_point = 96
    #
    #
    cn_holidays = holidays.CountryHoliday('CN')
    #
    system_date = EpSystem.get_system_date()  # 输出 eg:2025-01-01
    dt1 = datetime.datetime.strptime("2024-01-01", "%Y-%m-%d")
    dt2 = datetime.datetime.strptime(system_date, "%Y-%m-%d")
    gaps = dt2 - dt1
    gap_days = gaps.days
    #
    logger.info(f"system_date: {system_date}")
    logger.info(f"gap_days: {gap_days}")
    #
    # gap_days = 500
    #
    # system_date - 1: 所有字段
    data = EpData.get_history_data(scope="weather,plant,market", days=gap_days)
    # data = EpData.get_history_data(scope=["weather","plant","market"], days=gap_days)
    #
    #
    plant = data.get("plant")
    market = data.get("market")
    weather = data.get("weather")
    #
    plant = sorted(plant, key=lambda x: x["timestamp"])
    market = sorted(market, key=lambda x: x["timestamp"])
    #
    #
    logger.info(f"plant: {len(plant), plant[0], plant[-1]}")
    logger.info(f"market: {len(market), market[0], market[-1]}")
    #
    #
    plant = pd.DataFrame.from_dict(plant)
    market = pd.DataFrame.from_dict(market)
    #
    market = process_market(market, day_point=day_point)
    #
    weather, wea_keys = process_weather(weather)
    # for key in wea_keys:
    #     key = key + "_mean"
    #     weather[f"{key}_3"] = smooth_left_data(weather[key].to_numpy(), wind_half=3)
    #     weather[f"{key}_5"] = smooth_left_data(weather[key].to_numpy(), wind_half=5)
    #     # weather[f"{key}_10"] = smooth_left_data(weather[key].to_numpy(), wind_half=10)
    # #
    #
    #
    #
    all_datas, float_names, cate_names = get_data_label(market, plant, weather=weather, istrain=True)
    #
    #
    #
    logger.info(f"all_datas: {len(all_datas), len(market), len(plant)}")
    logger.info(f"float_names: {float_names}")
    #
    #
    #
    for name in cate_names:
        all_datas[name] = all_datas[name].astype('category')
    for name in float_names:
        all_datas[name] = all_datas[name].astype(float)
    #
    #
    #
    day_valid = day_point * 15
    #
    #
    train_data = all_datas[:-day_valid].reset_index(drop=True)
    valid_data = all_datas[-day_valid:].reset_index(drop=True)
    #
    X_all_train, x_train, x_valid = all_datas[float_names + cate_names], train_data[float_names + cate_names], \
    valid_data[float_names + cate_names]
    #
    #
    #
    lr_riqian = 0.15
    lr_shishi = 0.12
    #
    target = "before_price"
    y_all_train, y_train, y_valid = all_datas[target], train_data[target], valid_data[target]
    #
    y_valid_pred_before, y_train_pred_before, model_before = simple_reg_price(x_train, y_train, x_valid, y_valid,
                                                                              cate_fea=cate_names, lr=lr_riqian)
    loss_valid = np.mean((y_valid_pred_before - y_valid) ** 2)
    loss_train = np.mean((y_train_pred_before - y_train) ** 2)
    logger.info(f"riqian: best_iter: {model_before.best_iteration}, loss_valid: {loss_valid}, loss_train: {loss_train}")
    model_before = eval_reg_price(X_all_train, y_all_train, model_before.best_iteration, cate_fea=cate_names,
                                  lr=lr_riqian)
    #
    #
    #
    target = "real_price"  # before_price, real_price, diff_price
    y_all_train, y_train, y_valid = all_datas[target], train_data[target], valid_data[target]
    #
    y_valid_pred_shishi, y_train_pred_shishi, model_real = simple_reg_price(x_train, y_train, x_valid, y_valid,
                                                                            cate_fea=cate_names, lr=lr_shishi)
    loss_valid = np.mean((y_valid_pred_shishi - y_valid) ** 2)
    loss_train = np.mean((y_train_pred_shishi - y_train) ** 2)
    logger.info(f"shishi: best_iter: {model_real.best_iteration}, loss_valid: {loss_valid}, loss_train: {loss_train}")
    model_real = eval_reg_price(X_all_train, y_all_train, model_real.best_iteration, cate_fea=cate_names, lr=lr_shishi)
    #
    #
    #
    reqian_res = {}
    reqian_res['model_before'] = model_before
    reqian_res['float_names'] = float_names
    reqian_res['cate_names'] = cate_names
    reqian_res['model_real'] = model_real
    #
    #
    #
    base = "./tmp"
    if not os.path.exists(base):
        os.makedirs(base)
    #
    with open(f'{base}/riqian_price.pickle', 'wb') as handle:
        pickle.dump(reqian_res, handle)
    #
    #
    logger.info("train done!")
    #
    EpSystem.call_train_done()


#


#
#
inited = False
riqian_model = None
riqian_cate = None
riqian_float = None
shishi_model = None
cn_holidays = holidays.CountryHoliday('CN')


def initialize():
    global inited, riqian_model, riqian_cate, riqian_float, shishi_model
    #
    #
    #
    base = "./tmp"
    path = f'{base}/riqian_price.pickle'
    #
    logger.info(f"loading model from {path}")
    #
    #
    with open(path, 'rb') as f:
        # riqian_res = pickle.load(f)ode-file/20250522041137_submit_0521.py/riqian_price.pickle'
        #
        riqian_res = pickle.load(f)
        riqian_model = riqian_res["model_before"]
        riqian_cate = riqian_res["cate_names"]
        riqian_float = riqian_res["float_names"]
        shishi_model = riqian_res["model_real"]
    #
    #
    inited = True
    #


#


def get_baoliang(riqian_pred, shishi_pred, power_pred):
    #
    min_report, max_report, step = 0, 50, 0.1

    #
    def get_factor(diff1, diff2, p_power):
        # [0, 1000] -> [1, 0.1]
        #
        maxv = 250
        diff1 = min(diff1, maxv)
        factor1 = ((maxv - diff1) / maxv) ** 2 + 0.00
        #
        rate = min(diff2 / (0.4 * max(p_power, 0.1)), 3) + 0.00
        #
        return factor1 * rate

    #
    punish = 0.22

    def get_profit(baoliang, r_price, s_price, p_power, bad_point):
        #
        risk = 0
        profit_factor = (baoliang - p_power) * (r_price - s_price)
        #
        #
        punish_factor = punish
        #
        if bad_point:
            punish_factor = punish_factor * 100
        #
        normal = abs(baoliang - p_power) / (max_report - p_power) if baoliang > p_power else (
            abs(baoliang - p_power) / p_power if p_power != 0 else 0)
        #
        if profit_factor > 0:
            profit_factor = min(abs(baoliang - p_power), 0.4 * p_power) * abs(r_price - s_price)
            factor = get_factor(abs(r_price - s_price), abs(baoliang - p_power), p_power)
            risk = punish_factor * abs(baoliang - p_power) * abs(r_price - s_price) * factor
            #
        profit_withdraw = profit_factor + p_power * r_price
        #
        #
        return profit_withdraw - risk
        # return baoliang * r_price + (p_power - baoliang) * s_price - punish * normal * abs(baoliang - p_power) * abs(r_price - s_price)

    #
    #
    day_point = 96
    baoliang_profit_map = []
    #
    for idx, (r_pred, s_pred, p_pred) in enumerate(zip(riqian_pred, shishi_pred, power_pred)):
        #
        # fadian = p_pred
        fadian = p_pred + 1.5
        # fadian = p_pred + 3.5
        #
        # bad_point = idx < 6 * 4 or idx > 22 * 4
        bad_point = idx < 4 * 4 or idx > 22 * 4
        #
        except_profits = []
        baoliang = min_report
        #
        while baoliang < max_report:
            profit = get_profit(baoliang, r_pred, s_pred, fadian, bad_point)
            except_profits.append(profit)
            #
            baoliang += step
        baoliang_profit_map.append(except_profits)
        #
    #
    # order1_max = 4.5
    order1_max = 3.7
    # order1_max = 3
    #
    range_skip = int(order1_max / step)
    #
    #
    posi_num = int(max_report / step)
    #
    start = 0
    pre_best = [[i for i in range(posi_num)]]
    for point in range(start + 1, start + day_point):
        best_pre = []
        for idx in range(posi_num):
            min_pos, max_pos = max(0, idx - range_skip), min(posi_num - 1, idx + range_skip)
            index = np.argmax(baoliang_profit_map[point - 1][min_pos:max_pos]) + min_pos
            baoliang_profit_map[point][idx] += baoliang_profit_map[point - 1][index]
            best_pre.append(index)
        pre_best.append(best_pre)
    #
    last_max = np.argmax(baoliang_profit_map[start + day_point - 1])
    #
    pre_list = [last_max]
    for idx in range(len(pre_best) - 1, 0, -1):
        last_max = pre_best[idx][last_max]
        pre_list.append(last_max)
    pre_list.reverse()
    #
    baoliangs = [v * step for v in pre_list]
    #
    return baoliangs


#

def predict():
    global cn_holidays, inited, riqian_model, riqian_cate, riqian_float, shishi_model
    #
    # if not inited:
    #     initialize()
    # #
    initialize()
    #
    day_point = 96
    #
    target_date = EpSystem.get_system_date()
    #
    # system_date + 1: plant/weather
    data = EpData.get_predict_data(scope="plant,weather")
    #
    #
    if data is None or len(data) == 0:
        return None
    #
    plant = data["plant"]
    weather = data["weather"]
    #
    # system_date - 1: market
    data = EpData.get_history_data(scope="market", days=11)
    # data = EpData.get_history_data(scope=["market"], date=1)
    market = data["market"]
    #
    #
    plant = sorted(plant, key=lambda x: x["timestamp"])
    market = sorted(market, key=lambda x: x["timestamp"])
    #
    # logger.info(f"plant: {len(plant), plant}")
    logger.info(f"plant: {len(plant), plant[0], plant[-1]}")
    logger.info(f"market: {len(market), market[0], market[-1]}")
    #
    #
    plant = pd.DataFrame.from_dict(plant)
    market = pd.DataFrame.from_dict(market)
    #
    market = process_market(market, day_point=day_point)
    #
    market = market.tail(day_point).reset_index(drop=True)
    #
    #
    price_data, _, _ = get_data_label(market, plant, weather=None, istrain=False)
    #
    #
    logger.info(f"price_data: {len(price_data), price_data.head(2)}")
    #
    #
    for col in riqian_cate:
        price_data[col] = price_data[col].astype('category')
    for col in riqian_float:
        price_data[col] = price_data[col].astype('float')
    #
    #
    riqian_test = price_data[riqian_model.feature_name()]
    riqian_pred = list(riqian_model.predict(riqian_test))
    #
    shishi_test = price_data[shishi_model.feature_name()]
    shishi_pred = list(shishi_model.predict(shishi_test))
    #
    #
    fadianpred = [float(v) for v in price_data["power_pred"].tolist()]
    #
    baoliangs = get_baoliang(riqian_pred, shishi_pred, fadianpred)
    #
    center = 13 * 4
    baoliangs = [
        val * (abs(idx - center) ** 4 / 40000 + 0.45) if idx >= 10 * 4 and idx <= 16 * 4 else val for idx, val in
        enumerate(baoliangs)
    ]
    baoliangs = [f"{val:.2f}" for val in baoliangs]
    #
    return baoliangs
#


